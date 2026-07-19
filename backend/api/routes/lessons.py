"""Lessons Learned & Failure Intelligence Engine API routes."""
from fastapi import APIRouter
from typing import Optional

from services.lessons_agent import (
    get_lessons,
    get_proactive_warnings,
    analyze_patterns,
)

router = APIRouter()


@router.get("/")
async def list_lessons(
    incident_type: Optional[str] = None,
    asset_tag: Optional[str] = None,
    severity: Optional[str] = None,
    tag: Optional[str] = None,
):
    """Get lessons learned with optional filters."""
    return get_lessons(
        incident_type=incident_type,
        asset_tag=asset_tag,
        severity=severity,
        tag=tag,
    )


@router.get("/warnings")
async def proactive_warnings():
    """Get current active proactive warnings based on pattern matching."""
    return get_proactive_warnings()


@router.get("/patterns")
async def pattern_analysis(asset_tag: Optional[str] = None):
    """Run AI pattern analysis across lessons learned."""
    return await analyze_patterns(asset_tag=asset_tag)
