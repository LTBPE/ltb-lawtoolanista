# Court Monitor

An Azure-hosted web change monitoring system for LawToolbox that tracks ~1,000 court
website URLs for changes to docketing rules. When a relevant change is detected, it
creates a SharePoint list item and sends an email notification via Microsoft Graph.

---

## Architecture Overview

```
Azure Timer (weekly)
    |
    v
CRAWL_QUEUE (one message per court)
    |
    v
crawl_function (per-URL, queue-triggered)
  - Fetches page with HTTPX (Playwright for JS sites)
  - Extracts text with Trafilatura
  - Hashes content; if changed -> saves blobs
    |
    v
ANALYZE_QUEUE
    |
    v
analyze_function (queue-triggered)
  - Loads old/new blobs, generates unified diff
  - Calls Claude Haiku to classify relevance
  - If relevant: creates SharePoint item + sends email
    |
    +-> Azure SQL (courts, scan_history, changes, alert_config)
    +-> Azure Blob Storage (page text snapshots)
    +-> SharePoint list (Court Rule Changes)
    +-> Email via Microsoft Graph sendMail

Management API (HTTP, Azure Functions)
  - CRUD for courts
  - View changes + update review status
  - Dashboard stats
  - Alert config

Frontend (React + Vite, Azure Static Web Apps)
  - Dashboard, Courts, Changes, Settings pages
```

---

## Prerequisites

- Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
- Azure Developer CLI (AZD): https://aka.ms/azd
- Python 3.11: https://www.python.org/downloads/
- Node.js 18+: https://nodejs.org/
- Azure Functions Core Tools v4: https://github.com/Azure/azure-functions-core-tools
- An Azure subscription with Contributor access
- A Microsoft 365 tenant with SharePoint access
  (courtdeadlines.sharepoint.com/sites/tb.LTB_Austin)
- An Anthropic API key

---

## First-Time Setup

### 1. Clone and authenticate

```bash
git clone <repo-url>
cd court-monitor
az login
azd auth login
```

### 2. Provision and deploy

```bash
# Provision all Azure resources + deploy function app and frontend
azd up

# When prompted, provide:
#   sqlAdminPassword   - strong password for SQL Server admin
#   anthropicApiKey    - your sk-ant-... key
#   graphTenantId      - Azure AD tenant ID
#   graphClientId      - app registration client ID
#   graphClientSecret  - app registration client secret
```

This creates:
- Storage Account (blobs + queues)
- Azure SQL Server + Database (Basic tier)
- Function App (Python 3.11, Consumption plan)
- Static Web App (Free tier)
- Key Vault (secrets stored, KV references in app settings)
- Application Insights

### 3. Run database migrations

```bash
cd backend
pip install -r requirements.txt

# Set connection string for local migration run
export AZURE_SQL_CONNECTION_STRING="<connection-string-from-Key-Vault>"

cd db
alembic upgrade head
```

### 4. Install Playwright on the Function App

Playwright requires browser binaries. After the first deployment, run:

```bash
az functionapp config appsettings set \
  --name <function-app-name> \
  --resource-group <rg-name> \
  --settings "POST_BUILD_COMMAND=playwright install chromium --with-deps"
```

Or SSH into the function app console and run:
```bash
playwright install chromium --with-deps
```

For automated deployment, the `playwright_setup.sh` startup script approach:
```bash
# In the Function App -> Configuration -> Startup Command:
bash /home/site/wwwroot/playwright_setup.sh
```

Create `backend/playwright_setup.sh`:
```bash
#!/bin/bash
playwright install chromium --with-deps 2>&1 || true
```

### 5. Set up SharePoint

```bash
cd scripts

# Set credentials
export GRAPH_TENANT_ID=<tenant-id>
export GRAPH_CLIENT_ID=<client-id>
export GRAPH_CLIENT_SECRET=<client-secret>

python setup_sharepoint.py
```

This will print `SHAREPOINT_SITE_ID` and `SHAREPOINT_LIST_ID`. Add them to the
Function App settings (or Key Vault) and update your local.settings.json.

### 6. Import court URLs

Prepare a CSV with columns: `name,url,state,court_type,category,notes`

```bash
cd scripts

# Get your function app host key from:
# Azure Portal -> Function App -> App keys -> _master

python import_urls.py \
  --file courts.csv \
  --api-url https://<function-app>.azurewebsites.net/api \
  --key <function-host-key>
```

Dry-run first to validate:
```bash
python import_urls.py --file courts.csv --api-url ... --key ... --dry-run
```

---

## Local Development

### Backend (Function App)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Copy and fill in local settings
copy local.settings.json.example local.settings.json
# Edit local.settings.json with your values

# Run locally
func start
```

### Frontend

```bash
cd frontend
npm install

# Create .env.local
echo "VITE_API_URL=http://localhost:7071" > .env.local
echo "VITE_FUNCTION_KEY=" >> .env.local

npm run dev
# Open http://localhost:5173
```

---

## How to Add a Court Manually

Option 1 - Via the portal:
1. Open the frontend at https://<static-web-app>.azurestaticapps.net
2. Go to Courts -> Add Court
3. Fill in Name, URL, Type, State, Category
4. Check "Requires JavaScript" if the site loads content dynamically

Option 2 - Via the API:
```bash
curl -X POST \
  "https://<func>.azurewebsites.net/api/courts?code=<key>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Travis County District Court",
    "url": "https://www.traviscountytx.gov/district-clerk/filing-procedures",
    "court_type": "state",
    "state": "TX",
    "category": "civil"
  }'
```

---

## How to Trigger a Manual Scan

Option 1 - Via the portal:
1. Go to Courts page
2. Click "Scan Now" next to the court

Option 2 - Via the API:
```bash
curl -X POST \
  "https://<func>.azurewebsites.net/api/courts/<court-id>/scan?code=<key>"
```

The court is enqueued to the crawl queue and processed within 1-2 minutes.

---

## Environment Variables Reference

| Variable | Description | Default |
|---|---|---|
| `AzureWebJobsStorage` | Azure Storage connection string (blobs + queues) | required |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | required for AI |
| `AI_ENABLED` | Enable Claude AI analysis | `true` |
| `GRAPH_TENANT_ID` | Azure AD tenant ID | required |
| `GRAPH_CLIENT_ID` | App registration client ID | required |
| `GRAPH_CLIENT_SECRET` | App registration client secret | required |
| `GRAPH_SENDER_EMAIL` | From address for notifications | `copilotspeaking@lawtoolbox.com` |
| `SHAREPOINT_SITE_ID` | SharePoint site ID (from setup script) | required |
| `SHAREPOINT_LIST_ID` | SharePoint list ID (from setup script) | required |
| `AZURE_SQL_CONNECTION_STRING` | ODBC connection string for Azure SQL | required |
| `BLOB_CONTAINER_NAME` | Blob container for page snapshots | `court-snapshots` |
| `CRAWL_QUEUE_NAME` | Storage queue for crawl jobs | `crawl-queue` |
| `ANALYZE_QUEUE_NAME` | Storage queue for analysis jobs | `analyze-queue` |
| `SCAN_CONCURRENCY` | Max parallel crawls | `20` |
| `MIN_DIFF_LINES` | Min changed lines to trigger analysis | `3` |
| `CRAWL_DELAY_SECONDS` | Delay between HTTP requests | `1.0` |
| `CRAWL_TIMEOUT_SECONDS` | HTTP + Playwright timeout | `30` |
| `MANAGEMENT_PORTAL_URL` | Frontend URL (used in email footer) | Static Web App URL |

---

## App Registration Permissions Required

In Azure AD, the app registration needs these Microsoft Graph API permissions
(Application, not Delegated):

- `Sites.ReadWrite.All` - Create SharePoint list items
- `Mail.Send` - Send email via sendMail as the sender account

After granting permissions, an admin must click "Grant admin consent".

---

## Cost Estimate

All resources on the smallest viable SKUs:

| Resource | SKU | Estimated Cost |
|---|---|---|
| Azure Functions | Consumption (Y1) | ~$0-2/mo (first 1M executions free) |
| Azure SQL | Basic (5 DTU) | ~$5/mo |
| Storage Account | Standard_LRS | ~$0.50/mo |
| Static Web App | Free | $0 |
| Key Vault | Standard | ~$0.10/mo |
| Application Insights | Pay-as-you-go | ~$0-3/mo |
| **Total** | | **~$6-11/mo** |

---

## Monitoring

- Application Insights: Function App -> Monitor -> Application Insights
- Failed queue messages (poison queue): Check `crawl-queue-poison` and
  `analyze-queue-poison` in Storage Account
- Court errors: Courts page -> consecutive_errors column
- Scan history per court: GET /api/courts/{id}
