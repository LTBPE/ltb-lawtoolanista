"""
HTTP API blueprint for court management, change log, and settings.

All routes are under /api/ and require function-level auth.
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

import azure.functions as func
from sqlalchemy import func as sqlfunc, select, desc, and_, or_, text as sa_text

from shared.config import config
from shared.database import get_db_session
from shared.models import AlertConfig, Change, Court, ScanHistory
from shared.schemas import (
    AlertConfigOut,
    AlertConfigUpdate,
    ChangeListOut,
    ChangeOut,
    ChangeStatusUpdate,
    CourtCreate,
    CourtListOut,
    CourtOut,
    CourtUpdate,
    DashboardOut,
    HealthOut,
    ScanHistoryOut,
)

logger = logging.getLogger(__name__)

bp = func.Blueprint()

_DEFAULT_PAGE_SIZE = 50
_MAX_PAGE_SIZE = 200


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _json_response(
    data: Any, status_code: int = 200
) -> func.HttpResponse:
    """Return an HttpResponse with JSON body."""
    if hasattr(data, "model_dump"):
        body = data.model_dump(mode="json")
    elif isinstance(data, dict):
        body = data
    else:
        body = data
    return func.HttpResponse(
        body=json.dumps(body, default=str),
        status_code=status_code,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )


def _error_response(message: str, status_code: int = 400) -> func.HttpResponse:
    return _json_response({"error": message}, status_code)


def _parse_int_param(
    req: func.HttpRequest, name: str, default: int
) -> int:
    val = req.params.get(name, "")
    try:
        return int(val) if val else default
    except ValueError:
        return default


# ---------------------------------------------------------------------------
# Courts
# ---------------------------------------------------------------------------


@bp.route(route="courts", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
async def list_courts(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/courts - list courts with pagination and filtering."""
    page = max(1, _parse_int_param(req, "page", 1))
    page_size = min(
        _MAX_PAGE_SIZE, max(1, _parse_int_param(req, "page_size", _DEFAULT_PAGE_SIZE))
    )
    state_filter = req.params.get("state", "").upper() or None
    active_filter = req.params.get("active", "").lower()
    court_type_filter = req.params.get("court_type", "") or None

    async with get_db_session() as session:
        query = select(Court)
        if state_filter:
            query = query.where(Court.state == state_filter)
        if active_filter in ("true", "1"):
            query = query.where(Court.active == True)
        elif active_filter in ("false", "0"):
            query = query.where(Court.active == False)
        if court_type_filter:
            query = query.where(Court.court_type == court_type_filter)

        total_result = await session.execute(
            select(sqlfunc.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()

        courts_result = await session.execute(
            query.order_by(Court.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        courts = courts_result.scalars().all()

        items = []
        for court in courts:
            scans_result = await session.execute(
                select(ScanHistory)
                .where(ScanHistory.court_id == court.id)
                .order_by(desc(ScanHistory.scanned_at))
                .limit(5)
            )
            recent = scans_result.scalars().all()
            court_out = CourtOut.model_validate(court)
            court_out.recent_scans = [
                ScanHistoryOut.model_validate(s) for s in recent
            ]
            items.append(court_out)

    return _json_response(
        CourtListOut(items=items, total=total, page=page, page_size=page_size)
    )


@bp.route(route="courts", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
async def create_court(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/courts - create a new court."""
    try:
        body = req.get_json()
        court_data = CourtCreate(**body)
    except Exception as exc:
        return _error_response(f"Invalid request body: {exc}")

    async with get_db_session() as session:
        # Check for duplicate URL
        existing = await session.execute(
            select(Court).where(Court.url == court_data.url)
        )
        if existing.scalars().first():
            return _error_response(
                f"A court with URL {court_data.url!r} already exists", 409
            )

        court = Court(**court_data.model_dump())
        session.add(court)
        await session.flush()
        court_id = court.id

    async with get_db_session() as session:
        court = await session.get(Court, court_id)
        court_out = CourtOut.model_validate(court)

    return _json_response(court_out, 201)


@bp.route(route="courts/{court_id}", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
async def get_court(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/courts/{id} - get a court with recent scan history."""
    try:
        court_id = int(req.route_params["court_id"])
    except ValueError:
        return _error_response("Invalid court ID", 400)

    async with get_db_session() as session:
        court = await session.get(Court, court_id)
        if court is None:
            return _error_response("Court not found", 404)

        scans_result = await session.execute(
            select(ScanHistory)
            .where(ScanHistory.court_id == court_id)
            .order_by(desc(ScanHistory.scanned_at))
            .limit(20)
        )
        recent = scans_result.scalars().all()
        court_out = CourtOut.model_validate(court)
        court_out.recent_scans = [ScanHistoryOut.model_validate(s) for s in recent]

    return _json_response(court_out)


@bp.route(route="courts/{court_id}", methods=["PUT"], auth_level=func.AuthLevel.FUNCTION)
async def update_court(req: func.HttpRequest) -> func.HttpResponse:
    """PUT /api/courts/{id} - update a court."""
    try:
        court_id = int(req.route_params["court_id"])
        body = req.get_json()
        update_data = CourtUpdate(**body)
    except Exception as exc:
        return _error_response(f"Invalid request: {exc}")

    async with get_db_session() as session:
        court = await session.get(Court, court_id)
        if court is None:
            return _error_response("Court not found", 404)

        for field, value in update_data.model_dump(exclude_unset=True).items():
            setattr(court, field, value)

        await session.commit()
        await session.refresh(court)
        court_out = CourtOut.model_validate(court)

    return _json_response(court_out)


@bp.route(
    route="courts/{court_id}", methods=["DELETE"], auth_level=func.AuthLevel.FUNCTION
)
async def delete_court(req: func.HttpRequest) -> func.HttpResponse:
    """DELETE /api/courts/{id} - soft delete (set active=False)."""
    try:
        court_id = int(req.route_params["court_id"])
    except ValueError:
        return _error_response("Invalid court ID", 400)

    async with get_db_session() as session:
        court = await session.get(Court, court_id)
        if court is None:
            return _error_response("Court not found", 404)

        court.active = False
        await session.commit()

    return _json_response({"message": "Court deactivated"})


@bp.route(
    route="courts/{court_id}/scan",
    methods=["POST"],
    auth_level=func.AuthLevel.FUNCTION,
)
async def trigger_scan(req: func.HttpRequest) -> func.HttpResponse:
    """POST /api/courts/{id}/scan - trigger an immediate scan."""
    from azure.storage.queue.aio import QueueClient as AsyncQueueClient

    try:
        court_id = int(req.route_params["court_id"])
    except ValueError:
        return _error_response("Invalid court ID", 400)

    async with get_db_session() as session:
        court = await session.get(Court, court_id)
        if court is None:
            return _error_response("Court not found", 404)

    message = json.dumps({"court_id": court_id})
    queue_client = AsyncQueueClient.from_connection_string(
        conn_str=config.AZURE_WEBJOBS_STORAGE,
        queue_name=config.CRAWL_QUEUE_NAME,
    )
    try:
        await queue_client.create_queue()
    except Exception:
        pass
    await queue_client.send_message(message)
    await queue_client.close()

    return _json_response({"message": f"Scan triggered for court {court_id}"})


# ---------------------------------------------------------------------------
# Changes
# ---------------------------------------------------------------------------


@bp.route(route="changes", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
async def list_changes(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/changes - list changes with filtering and pagination."""
    page = max(1, _parse_int_param(req, "page", 1))
    page_size = min(
        _MAX_PAGE_SIZE, max(1, _parse_int_param(req, "page_size", _DEFAULT_PAGE_SIZE))
    )
    status_filter = req.params.get("status", "") or None
    priority_filter = req.params.get("priority", "") or None
    date_from = req.params.get("date_from", "") or None
    date_to = req.params.get("date_to", "") or None

    async with get_db_session() as session:
        query = select(Change)
        if status_filter:
            query = query.where(Change.status == status_filter)
        if priority_filter:
            query = query.where(Change.ai_priority == priority_filter)
        if date_from:
            try:
                query = query.where(
                    Change.detected_at >= datetime.fromisoformat(date_from)
                )
            except ValueError:
                pass
        if date_to:
            try:
                query = query.where(
                    Change.detected_at <= datetime.fromisoformat(date_to)
                )
            except ValueError:
                pass

        total_result = await session.execute(
            select(sqlfunc.count()).select_from(query.subquery())
        )
        total = total_result.scalar_one()

        changes_result = await session.execute(
            query.order_by(desc(Change.detected_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        changes = changes_result.scalars().all()

        items = []
        for change in changes:
            court = await session.get(Court, change.court_id)
            out = ChangeOut.model_validate(change)
            out.court_name = court.name if court else None
            out.court_url = court.url if court else None
            items.append(out)

    return _json_response(
        ChangeListOut(items=items, total=total, page=page, page_size=page_size)
    )


@bp.route(
    route="changes/{change_id}", methods=["GET"], auth_level=func.AuthLevel.FUNCTION
)
async def get_change(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/changes/{id} - get a change with full diff."""
    try:
        change_id = int(req.route_params["change_id"])
    except ValueError:
        return _error_response("Invalid change ID", 400)

    async with get_db_session() as session:
        change = await session.get(Change, change_id)
        if change is None:
            return _error_response("Change not found", 404)

        court = await session.get(Court, change.court_id)
        out = ChangeOut.model_validate(change)
        out.court_name = court.name if court else None
        out.court_url = court.url if court else None

    return _json_response(out)


@bp.route(
    route="changes/{change_id}/status",
    methods=["PUT"],
    auth_level=func.AuthLevel.FUNCTION,
)
async def update_change_status(req: func.HttpRequest) -> func.HttpResponse:
    """PUT /api/changes/{id}/status - update change review status."""
    try:
        change_id = int(req.route_params["change_id"])
        body = req.get_json()
        update = ChangeStatusUpdate(**body)
    except Exception as exc:
        return _error_response(f"Invalid request: {exc}")

    async with get_db_session() as session:
        change = await session.get(Change, change_id)
        if change is None:
            return _error_response("Change not found", 404)

        change.status = update.status
        if update.reviewed_by:
            change.reviewed_by = update.reviewed_by
        if update.resolution_notes:
            change.resolution_notes = update.resolution_notes
        change.reviewed_at = datetime.utcnow()

        await session.commit()
        court = await session.get(Court, change.court_id)
        out = ChangeOut.model_validate(change)
        out.court_name = court.name if court else None
        out.court_url = court.url if court else None

    return _json_response(out)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@bp.route(route="dashboard", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
async def get_dashboard(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/dashboard - aggregated statistics."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    async with get_db_session() as session:
        total_courts = (
            await session.execute(select(sqlfunc.count(Court.id)))
        ).scalar_one()

        active_courts = (
            await session.execute(
                select(sqlfunc.count(Court.id)).where(Court.active == True)
            )
        ).scalar_one()

        scanned_today = (
            await session.execute(
                select(sqlfunc.count(ScanHistory.id)).where(
                    ScanHistory.scanned_at >= today_start
                )
            )
        ).scalar_one()

        scanned_this_week = (
            await session.execute(
                select(sqlfunc.count(ScanHistory.id)).where(
                    ScanHistory.scanned_at >= week_start
                )
            )
        ).scalar_one()

        changes_new = (
            await session.execute(
                select(sqlfunc.count(Change.id)).where(Change.status == "new")
            )
        ).scalar_one()

        changes_this_week = (
            await session.execute(
                select(sqlfunc.count(Change.id)).where(
                    Change.detected_at >= week_start
                )
            )
        ).scalar_one()

        error_count = (
            await session.execute(
                select(sqlfunc.count(ScanHistory.id)).where(
                    and_(
                        ScanHistory.status.in_(["error", "timeout"]),
                        ScanHistory.scanned_at >= week_start,
                    )
                )
            )
        ).scalar_one()

        last_scan_result = await session.execute(
            select(sqlfunc.max(ScanHistory.scanned_at))
        )
        last_scan_at = last_scan_result.scalar_one()

    return _json_response(
        DashboardOut(
            total_courts=total_courts,
            active_courts=active_courts,
            scanned_today=scanned_today,
            scanned_this_week=scanned_this_week,
            changes_new=changes_new,
            changes_this_week=changes_this_week,
            error_count=error_count,
            last_scan_at=last_scan_at,
        )
    )


# ---------------------------------------------------------------------------
# Alert Config
# ---------------------------------------------------------------------------


@bp.route(route="config", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
async def get_config(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/config - get alert configuration."""
    async with get_db_session() as session:
        result = await session.execute(select(AlertConfig).limit(1))
        alert_config = result.scalars().first()

        if alert_config is None:
            # Create default config
            alert_config = AlertConfig(
                email_recipients="",
                notify_immediately=True,
                min_priority="low",
                ai_filter_enabled=True,
            )
            session.add(alert_config)
            await session.commit()
            await session.refresh(alert_config)

    return _json_response(AlertConfigOut.model_validate(alert_config))


@bp.route(route="config", methods=["PUT"], auth_level=func.AuthLevel.FUNCTION)
async def update_config(req: func.HttpRequest) -> func.HttpResponse:
    """PUT /api/config - update alert configuration."""
    try:
        body = req.get_json()
        update_data = AlertConfigUpdate(**body)
    except Exception as exc:
        return _error_response(f"Invalid request body: {exc}")

    async with get_db_session() as session:
        result = await session.execute(select(AlertConfig).limit(1))
        alert_config = result.scalars().first()

        if alert_config is None:
            alert_config = AlertConfig()
            session.add(alert_config)

        for field, value in update_data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(alert_config, field, value)

        await session.commit()
        await session.refresh(alert_config)

    return _json_response(AlertConfigOut.model_validate(alert_config))


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@bp.route(route="health", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """GET /api/health - simple health check."""
    db_status = "ok"
    storage_status = "ok"

    try:
        from shared.database import get_engine
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(sa_text("SELECT 1"))
    except Exception as exc:
        logger.warning("DB health check failed: %s", exc)
        db_status = f"error: {exc}"

    try:
        from azure.storage.blob.aio import BlobServiceClient
        blob_client = BlobServiceClient.from_connection_string(
            config.AZURE_WEBJOBS_STORAGE
        )
        async with blob_client:
            pass
        storage_status = "ok"
    except Exception as exc:
        logger.warning("Storage health check failed: %s", exc)
        storage_status = f"error: {exc}"

    status = "ok" if db_status == "ok" and storage_status == "ok" else "degraded"
    http_status = 200 if status == "ok" else 503

    return _json_response(
        HealthOut(status=status, database=db_status, storage=storage_status),
        http_status,
    )
