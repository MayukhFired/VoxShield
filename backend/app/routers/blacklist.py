from fastapi import APIRouter, HTTPException, Query, Request, Header
from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from app.security import enforce_rate_limit, normalize_phone_number, require_admin

router = APIRouter()


class ReportRequest(BaseModel):
    phone_number: str
    confidence_score: Optional[float] = None
    notes: Optional[str] = None

    @validator("phone_number")
    def validate_phone_number(cls, value):
        try:
            return normalize_phone_number(value)
        except ValueError as error:
            raise ValueError(str(error))

    @validator("confidence_score")
    def validate_confidence(cls, value):
        if value is not None and not 0 <= value <= 1:
            raise ValueError("confidence_score must be between 0 and 1")
        return value

    @validator("notes")
    def limit_notes(cls, value):
        if value and len(value) > 500:
            raise ValueError("notes must be 500 characters or fewer")
        return value


class BlacklistEntry(BaseModel):
    phone_number: str
    reports_count: int
    first_reported: str
    last_reported: str
    avg_confidence: float
    status: str  # "suspicious" | "confirmed"


@router.post("/report")
async def report_number(request: Request, report: ReportRequest):
    """Report a phone number as a potential scam."""
    enforce_rate_limit(request, "blacklist-report")
    from app.database import add_report
    
    result = await add_report(
        phone_number=report.phone_number,
        confidence_score=report.confidence_score or 0.0,
        notes=report.notes,
    )
    return result


@router.get("/check/{phone_number}")
async def check_number(request: Request, phone_number: str):
    """Check if a phone number is in the blacklist. Fast lookup (<50ms)."""
    enforce_rate_limit(request, "blacklist-check")
    try:
        phone_number = normalize_phone_number(phone_number)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    from app.database import check_blacklist
    
    result = await check_blacklist(phone_number)
    return result


@router.get("/list")
async def list_blacklisted(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("reports_count", pattern="^(reports_count|last_reported|first_reported)$"),
):
    """Get paginated list of blacklisted numbers."""
    from app.database import get_blacklist_page
    
    # The public directory intentionally exposes only independently confirmed
    # entries; suspected reports remain visible only to the reporter/moderator.
    result = await get_blacklist_page(page=page, page_size=page_size, sort_by=sort_by, status="confirmed")
    return result


@router.get("/search")
async def search_numbers(request: Request, q: str = Query(..., min_length=3, max_length=20)):
    """Search blacklisted numbers by prefix or partial match."""
    enforce_rate_limit(request, "blacklist-search")
    from app.database import search_blacklist
    
    result = await search_blacklist(query=q)
    return result


@router.post("/confirm/{phone_number}")
async def confirm_number(
    request: Request,
    phone_number: str,
    x_admin_token: Optional[str] = Header(None),
):
    """Moderator-only confirmation; anonymous reports never confirm a number."""
    enforce_rate_limit(request, "blacklist-moderation")
    require_admin(x_admin_token)
    try:
        phone_number = normalize_phone_number(phone_number)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    from app.database import confirm_blacklist_number
    entry = await confirm_blacklist_number(phone_number)
    if not entry:
        raise HTTPException(status_code=404, detail="No report exists for this phone number.")
    return {"success": True, "entry": entry}
