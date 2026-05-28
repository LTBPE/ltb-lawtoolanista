"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Court schemas
# ---------------------------------------------------------------------------


class CourtBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=2048)
    court_type: str = Field(default="other")
    state: Optional[str] = Field(default=None, max_length=2)
    category: str = Field(default="all")
    active: bool = True
    js_required: bool = False
    css_selector: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = None

    @field_validator("court_type")
    @classmethod
    def validate_court_type(cls, v: str) -> str:
        allowed = {"state", "federal", "bankruptcy", "appellate", "other"}
        if v not in allowed:
            raise ValueError(f"court_type must be one of {allowed}")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        allowed = {"civil", "criminal", "family", "probate", "all"}
        if v not in allowed:
            raise ValueError(f"category must be one of {allowed}")
        return v


class CourtCreate(CourtBase):
    pass


class CourtUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    url: Optional[str] = Field(default=None, min_length=1, max_length=2048)
    court_type: Optional[str] = None
    state: Optional[str] = Field(default=None, max_length=2)
    category: Optional[str] = None
    active: Optional[bool] = None
    js_required: Optional[bool] = None
    css_selector: Optional[str] = Field(default=None, max_length=500)
    notes: Optional[str] = None


class ScanHistoryOut(BaseModel):
    id: int
    court_id: int
    scanned_at: datetime
    content_hash: Optional[str]
    status: str
    error_message: Optional[str]
    response_time_ms: Optional[int]

    model_config = {"from_attributes": True}


class CourtOut(CourtBase):
    id: int
    last_scanned_at: Optional[datetime]
    last_content_hash: Optional[str]
    last_changed_at: Optional[datetime]
    consecutive_errors: int
    created_at: datetime
    updated_at: Optional[datetime]
    recent_scans: list[ScanHistoryOut] = []

    model_config = {"from_attributes": True}


class CourtListOut(BaseModel):
    items: list[CourtOut]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Change schemas
# ---------------------------------------------------------------------------


class ChangeStatusUpdate(BaseModel):
    status: str
    reviewed_by: Optional[str] = None
    resolution_notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"new", "in_review", "resolved", "false_positive"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class ChangeOut(BaseModel):
    id: int
    court_id: int
    detected_at: datetime
    old_snapshot_path: str
    new_snapshot_path: str
    diff_text: Optional[str]
    diff_line_count: int
    ai_is_relevant: Optional[bool]
    ai_summary: Optional[str]
    ai_category: Optional[str]
    ai_priority: Optional[str]
    ai_action: Optional[str]
    sharepoint_item_id: Optional[str]
    email_sent: bool
    status: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    resolution_notes: Optional[str]
    court_name: Optional[str] = None
    court_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ChangeListOut(BaseModel):
    items: list[ChangeOut]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Dashboard schema
# ---------------------------------------------------------------------------


class DashboardOut(BaseModel):
    total_courts: int
    active_courts: int
    scanned_today: int
    scanned_this_week: int
    changes_new: int
    changes_this_week: int
    error_count: int
    last_scan_at: Optional[datetime]


# ---------------------------------------------------------------------------
# AlertConfig schemas
# ---------------------------------------------------------------------------


class AlertConfigOut(BaseModel):
    id: int
    email_recipients: str
    notify_immediately: bool
    notify_digest_time: Optional[str]
    min_priority: str
    ai_filter_enabled: bool

    model_config = {"from_attributes": True}


class AlertConfigUpdate(BaseModel):
    email_recipients: Optional[str] = None
    notify_immediately: Optional[bool] = None
    notify_digest_time: Optional[str] = None
    min_priority: Optional[str] = None
    ai_filter_enabled: Optional[bool] = None

    @field_validator("min_priority")
    @classmethod
    def validate_min_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"low", "medium", "high"}
        if v not in allowed:
            raise ValueError(f"min_priority must be one of {allowed}")
        return v


# ---------------------------------------------------------------------------
# Health check schema
# ---------------------------------------------------------------------------


class HealthOut(BaseModel):
    status: str
    database: str
    storage: str
    version: str = "1.0.0"
