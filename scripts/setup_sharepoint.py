"""
One-time setup script to create the SharePoint list for court rule changes.

Run this once before deploying the function app:
    python setup_sharepoint.py

Requires environment variables:
    GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET
"""

import json
import os
import sys

import msal
import requests

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SHAREPOINT_HOST = "courtdeadlines.sharepoint.com"
SHAREPOINT_SITE_PATH = "/sites/tb.LTB_Austin"
LIST_NAME = "Court Rule Changes"

TENANT_ID = os.environ.get("GRAPH_TENANT_ID", "")
CLIENT_ID = os.environ.get("GRAPH_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GRAPH_CLIENT_SECRET", "")


def get_token() -> str:
    """Acquire an access token using client credentials flow."""
    app = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID,
        client_credential=CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    )
    result = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )
    if "access_token" not in result:
        error = result.get("error_description", result.get("error", "unknown"))
        print(f"ERROR: Failed to acquire token: {error}")
        sys.exit(1)
    return result["access_token"]


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def get_site_id(token: str) -> str:
    """Discover the SharePoint site ID."""
    url = f"{GRAPH_BASE}/sites/{SHAREPOINT_HOST}:{SHAREPOINT_SITE_PATH}"
    resp = requests.get(url, headers=headers(token))
    if not resp.ok:
        print(f"ERROR: Could not fetch site. Status {resp.status_code}: {resp.text}")
        sys.exit(1)
    data = resp.json()
    site_id = data["id"]
    print(f"Site ID discovered: {site_id}")
    return site_id


def create_list(token: str, site_id: str) -> str:
    """Create the 'Court Rule Changes' list and return its ID."""
    url = f"{GRAPH_BASE}/sites/{site_id}/lists"

    # Check if list already exists
    resp = requests.get(url, headers=headers(token))
    if resp.ok:
        for lst in resp.json().get("value", []):
            if lst.get("displayName") == LIST_NAME:
                list_id = lst["id"]
                print(f"List '{LIST_NAME}' already exists. ID: {list_id}")
                return list_id

    # Create the list
    payload = {
        "displayName": LIST_NAME,
        "list": {"template": "genericList"},
        "columns": [
            {"name": "Title", "text": {}},
            {"name": "CourtURL", "text": {"maxLength": 2048}},
            {"name": "DetectedDate", "dateTime": {"displayAs": "default"}},
            {"name": "Category", "text": {}},
            {"name": "Priority", "text": {}},
            {"name": "Summary", "text": {"allowMultipleLines": True}},
            {"name": "ActionRequired", "text": {"allowMultipleLines": True}},
            {"name": "DiffText", "text": {"allowMultipleLines": True, "maxLength": 5000}},
            {"name": "Status", "text": {}},
            {"name": "ChangeId", "text": {}},
        ],
    }

    resp = requests.post(url, headers=headers(token), json=payload)
    if not resp.ok:
        print(f"ERROR: Could not create list. Status {resp.status_code}: {resp.text}")
        sys.exit(1)

    list_id = resp.json()["id"]
    print(f"Created list '{LIST_NAME}'. ID: {list_id}")
    return list_id


def main() -> None:
    if not all([TENANT_ID, CLIENT_ID, CLIENT_SECRET]):
        print(
            "ERROR: Set GRAPH_TENANT_ID, GRAPH_CLIENT_ID, and GRAPH_CLIENT_SECRET "
            "environment variables before running this script."
        )
        sys.exit(1)

    print("Authenticating to Microsoft Graph...")
    token = get_token()

    print("Discovering SharePoint site ID...")
    site_id = get_site_id(token)

    print("Creating SharePoint list...")
    list_id = create_list(token, site_id)

    print("\n=== Add these to your environment variables / Key Vault ===")
    print(f"SHAREPOINT_SITE_ID={site_id}")
    print(f"SHAREPOINT_LIST_ID={list_id}")
    print("===========================================================\n")

    settings_hint = json.dumps(
        {"SHAREPOINT_SITE_ID": site_id, "SHAREPOINT_LIST_ID": list_id}, indent=2
    )
    print("JSON format for local.settings.json:")
    print(settings_hint)


if __name__ == "__main__":
    main()
