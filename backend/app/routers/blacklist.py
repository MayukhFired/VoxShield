from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter()


class ReportRequest(BaseModel):
    phone_number: str
    confidence_score: Optional[float] = None
    notes: Optional[str] = None


class BlacklistEntry(BaseModel):
    phone_number: str
    reports_count: int
    first_reported: str
    last_reported: str
    avg_confidence: float
    status: str  # "suspicious" | "confirmed"


@router.post("/report")
async def report_number(report: ReportRequest):
    """Report a phone number as a potential scam."""
    from app.database import add_report
    
    result = await add_report(
        phone_number=report.phone_number,
        confidence_score=report.confidence_score or 0.0,
        notes=report.notes,
    )
    return result


@router.get("/check/{phone_number}")
async def check_number(phone_number: str):
    """Check if a phone number is in the blacklist. Fast lookup (<50ms)."""
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
    
    result = await get_blacklist_page(page=page, page_size=page_size, sort_by=sort_by)
    return result


@router.get("/search")
async def search_numbers(q: str = Query(..., min_length=3)):
    """Search blacklisted numbers by prefix or partial match."""
    from app.database import search_blacklist
    
    result = await search_blacklist(query=q)
    return result
