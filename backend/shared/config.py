"""
Configuration module - reads all settings from environment variables.
"""

import os
from functools import lru_cache


class Settings:
    """Application settings loaded from environment variables."""

    # Anthropic / Claude AI
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
    AI_ENABLED: bool = os.environ.get("AI_ENABLED", "true").lower() == "true"

    # Microsoft Graph / SharePoint / Email
    GRAPH_TENANT_ID: str = os.environ.get("GRAPH_TENANT_ID", "")
    GRAPH_CLIENT_ID: str = os.environ.get("GRAPH_CLIENT_ID", "")
    GRAPH_CLIENT_SECRET: str = os.environ.get("GRAPH_CLIENT_SECRET", "")
    GRAPH_SENDER_EMAIL: str = os.environ.get(
        "GRAPH_SENDER_EMAIL", "copilotspeaking@lawtoolbox.com"
    )
    SHAREPOINT_SITE_ID: str = os.environ.get("SHAREPOINT_SITE_ID", "")
    SHAREPOINT_LIST_ID: str = os.environ.get("SHAREPOINT_LIST_ID", "")
    SHAREPOINT_HOST: str = "courtdeadlines.sharepoint.com"
    SHAREPOINT_SITE_PATH: str = "/sites/tb.LTB_Austin"

    # Azure SQL
    AZURE_SQL_CONNECTION_STRING: str = os.environ.get(
        "AZURE_SQL_CONNECTION_STRING", ""
    )

    # Azure Storage
    AZURE_WEBJOBS_STORAGE: str = os.environ.get("AzureWebJobsStorage", "")
    BLOB_CONTAINER_NAME: str = os.environ.get("BLOB_CONTAINER_NAME", "court-snapshots")
    CRAWL_QUEUE_NAME: str = os.environ.get("CRAWL_QUEUE_NAME", "crawl-queue")
    ANALYZE_QUEUE_NAME: str = os.environ.get("ANALYZE_QUEUE_NAME", "analyze-queue")

    # Crawl settings
    SCAN_CONCURRENCY: int = int(os.environ.get("SCAN_CONCURRENCY", "20"))
    MIN_DIFF_LINES: int = int(os.environ.get("MIN_DIFF_LINES", "3"))
    CRAWL_DELAY_SECONDS: float = float(os.environ.get("CRAWL_DELAY_SECONDS", "1.0"))
    CRAWL_TIMEOUT_SECONDS: int = int(os.environ.get("CRAWL_TIMEOUT_SECONDS", "30"))

    # Portal URL (used in email footer)
    MANAGEMENT_PORTAL_URL: str = os.environ.get(
        "MANAGEMENT_PORTAL_URL", "https://court-monitor.azurestaticapps.net"
    )

    # Graph API scope
    GRAPH_SCOPE: str = "https://graph.microsoft.com/.default"
    GRAPH_BASE_URL: str = "https://graph.microsoft.com/v1.0"

    @property
    def ai_configured(self) -> bool:
        """Return True if AI is both enabled and has an API key configured."""
        return self.AI_ENABLED and bool(self.ANTHROPIC_API_KEY)

    @property
    def graph_configured(self) -> bool:
        """Return True if all Graph API credentials are present."""
        return all([
            self.GRAPH_TENANT_ID,
            self.GRAPH_CLIENT_ID,
            self.GRAPH_CLIENT_SECRET,
        ])

    @property
    def sharepoint_configured(self) -> bool:
        """Return True if SharePoint IDs are configured."""
        return bool(self.SHAREPOINT_SITE_ID and self.SHAREPOINT_LIST_ID)

    @property
    def sql_configured(self) -> bool:
        """Return True if SQL connection string is present."""
        return bool(self.AZURE_SQL_CONNECTION_STRING)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


# Module-level convenience alias
config = get_settings()
