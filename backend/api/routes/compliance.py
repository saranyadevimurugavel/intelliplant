"""Quality & Regulatory Compliance Intelligence API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.compliance_agent import (
    get_compliance_gaps,
    get_compliance_health,
    generate_audit_package,
)

router = APIRouter()


class AuditPackageRequest(BaseModel):
    regulation: str


@router.get("/gaps")
async def list_compliance_gaps(
    regulation: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
):
    """Get compliance gaps with optional filters."""
    return get_compliance_gaps(regulation=regulation, severity=severity, status=status)


@router.get("/health")
async def compliance_health():
    """Get overall compliance health dashboard data."""
    return get_compliance_health()


@router.post("/audit-package")
async def create_audit_package(request: AuditPackageRequest):
    """Auto-generate a compliance audit evidence package."""
    if not request.regulation:
        raise HTTPException(status_code=400, detail="regulation is required.")
    return await generate_audit_package(request.regulation)
