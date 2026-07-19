"""Maintenance Intelligence & RCA Agent API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.maintenance_agent import (
    get_recommendations,
    get_maintenance_history,
    generate_rca,
    get_maintenance_schedule,
)

router = APIRouter()


class RCARequest(BaseModel):
    asset_tag: str
    failure_description: str


@router.get("/recommendations")
async def list_recommendations(asset_tag: Optional[str] = None, priority: Optional[str] = None):
    """Get predictive maintenance recommendations."""
    return get_recommendations(asset_tag=asset_tag, priority=priority)


@router.get("/history")
async def list_maintenance_history(asset_tag: Optional[str] = None):
    """Get maintenance work order history."""
    return get_maintenance_history(asset_tag=asset_tag)


@router.post("/rca")
async def run_rca(request: RCARequest):
    """Generate Root Cause Analysis for a reported failure."""
    if not request.asset_tag or not request.failure_description:
        raise HTTPException(status_code=400, detail="asset_tag and failure_description are required.")
    return await generate_rca(request.asset_tag, request.failure_description)


@router.get("/schedule")
async def get_schedule():
    """Get upcoming maintenance schedule."""
    return get_maintenance_schedule()
