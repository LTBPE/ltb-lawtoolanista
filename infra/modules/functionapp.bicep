@description('Azure region')
param location string

@description('Function App name')
param functionAppName string

@description('Storage account name for AzureWebJobsStorage')
param storageAccountName string

@description('Storage account connection string')
@secure()
param storageConnectionString string

@description('Key Vault name (for App Settings Key Vault references)')
param keyVaultName string

@description('Key Vault secret URI for Anthropic API key')
param anthropicApiKeySecretUri string = ''

@description('Key Vault secret URI for Graph client secret')
param graphClientSecretSecretUri string = ''

@description('Key Vault secret URI for SQL connection string')
param sqlConnectionStringSecretUri string = ''

@description('Microsoft Graph tenant ID (non-secret)')
param graphTenantId string = ''

@description('Microsoft Graph client ID (non-secret)')
param graphClientId string = ''

@description('Frontend URL for CORS and management portal')
param frontendUrl string = ''

var appServicePlanName = '${functionAppName}-plan'
var appInsightsName = '${functionAppName}-ai'

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    RetentionInDays: 30
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  kind: 'linux'
  properties: {
    reserved: true  // Required for Linux
  }
}

var anthropicAppSetting = !empty(anthropicApiKeySecretUri)
  ? '@Microsoft.KeyVault(SecretUri=${anthropicApiKeySecretUri})'
  : ''

var graphSecretAppSetting = !empty(graphClientSecretSecretUri)
  ? '@Microsoft.KeyVault(SecretUri=${graphClientSecretSecretUri})'
  : ''

var sqlConnAppSetting = !empty(sqlConnectionStringSecretUri)
  ? '@Microsoft.KeyVault(SecretUri=${sqlConnectionStringSecretUri})'
  : ''

resource functionApp 'Microsoft.Web/sites@2023-01-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      pythonVersion: '3.11'
      cors: {
        allowedOrigins: [
          'https://${frontendUrl}'
          'http://localhost:5173'
          'http://localhost:4280'
        ]
        supportCredentials: false
      }
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: storageConnectionString
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: storageConnectionString
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower(functionAppName)
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME_VERSION'
          value: '3.11'
        }
        {
          name: 'APPINSIGHTS_INSTRUMENTATIONKEY'
          value: appInsights.properties.InstrumentationKey
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'ANTHROPIC_API_KEY'
          value: anthropicAppSetting
        }
        {
          name: 'GRAPH_CLIENT_SECRET'
          value: graphSecretAppSetting
        }
        {
          name: 'AZURE_SQL_CONNECTION_STRING'
          value: sqlConnAppSetting
        }
        {
          name: 'GRAPH_TENANT_ID'
          value: graphTenantId
        }
        {
          name: 'GRAPH_CLIENT_ID'
          value: graphClientId
        }
        {
          name: 'GRAPH_SENDER_EMAIL'
          value: 'copilotspeaking@lawtoolbox.com'
        }
        {
          name: 'BLOB_CONTAINER_NAME'
          value: 'court-snapshots'
        }
        {
          name: 'CRAWL_QUEUE_NAME'
          value: 'crawl-queue'
        }
        {
          name: 'ANALYZE_QUEUE_NAME'
          value: 'analyze-queue'
        }
        {
          name: 'SCAN_CONCURRENCY'
          value: '20'
        }
        {
          name: 'MIN_DIFF_LINES'
          value: '3'
        }
        {
          name: 'CRAWL_DELAY_SECONDS'
          value: '1.0'
        }
        {
          name: 'AI_ENABLED'
          value: 'true'
        }
        {
          name: 'MANAGEMENT_PORTAL_URL'
          value: 'https://${frontendUrl}'
        }
        {
          name: 'WEBSITE_RUN_FROM_PACKAGE'
          value: '1'
        }
      ]
    }
  }
}

output functionAppId string = functionApp.id
output defaultHostname string = functionApp.properties.defaultHostName
output principalId string = functionApp.identity.principalId
