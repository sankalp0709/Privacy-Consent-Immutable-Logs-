"""
Compliance API Endpoints for BHIV Core
Provides REST API for consent management and audit log access
"""
from fastapi import APIRouter, Depends, HTTPException, Header, Request, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel

from compliance.consent_manager import consent_manager
from compliance.audit_logger import audit_logger
from utils.logger import get_logger

logger = get_logger(__name__)

# Define API models
class ConsentRequest(BaseModel):
    employee_id: str
    monitoring_enabled: bool
    retention_days: Optional[int] = None
    data_categories: Optional[List[str]] = None

class ConsentResponse(BaseModel):
    employee_id: str
    monitoring_enabled: bool
    retention_days: int
    expiration_date: str
    data_categories: List[str]
    last_updated: str
    status: str

class AuditLogRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    limit: int = 100

# Create router
router = APIRouter(
    prefix="/compliance",
    tags=["compliance"],
    responses={404: {"description": "Not found"}},
)

# Authentication dependency - replace with your actual auth system
async def verify_api_key(x_api_key: str = Header(...)):
    valid_key = "uniguru-dev-key-2025"  # Replace with secure key management
    if x_api_key != valid_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Consent endpoints
@router.post("/consent", response_model=ConsentResponse)
async def set_consent(
    request: Request,
    consent_data: ConsentRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Set consent preferences for an employee.
    Controls monitoring permissions and data retention.
    """
    try:
        # Get requester information
        requester_id = request.headers.get("X-User-ID", "system")
        client_ip = request.client.host if request.client else "unknown"
        
        # Set consent with audit logging
        result = consent_manager.set_consent(
            employee_id=consent_data.employee_id,
            monitoring_enabled=consent_data.monitoring_enabled,
            retention_days=consent_data.retention_days,
            data_categories=consent_data.data_categories,
            requester_id=requester_id
        )
        
        # Log additional details about the request
        audit_logger.log_event(
            user_id=requester_id,
            action="api_set_consent",
            resource=f"employee/{consent_data.employee_id}/consent",
            details={
                "ip_address": client_ip,
                "user_agent": request.headers.get("User-Agent", "unknown"),
                "request_data": consent_data.dict()
            }
        )
        
        return {
            **result,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error setting consent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to set consent: {str(e)}")

@router.get("/consent/{employee_id}", response_model=ConsentResponse)
async def get_consent(
    request: Request,
    employee_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get consent preferences for an employee.
    """
    try:
        # Get requester information
        requester_id = request.headers.get("X-User-ID", "system")
        client_ip = request.client.host if request.client else "unknown"
        
        # Get consent data
        result = consent_manager.get_consent(employee_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"No consent record found for employee {employee_id}")
        
        # Log access to consent data
        audit_logger.log_event(
            user_id=requester_id,
            action="api_get_consent",
            resource=f"employee/{employee_id}/consent",
            details={
                "ip_address": client_ip,
                "user_agent": request.headers.get("User-Agent", "unknown")
            }
        )
        
        return {
            **result,
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting consent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get consent: {str(e)}")

@router.get("/consent", response_model=List[ConsentResponse])
async def list_consents(
    request: Request,
    active_only: bool = Query(True, description="Only show active consents"),
    api_key: str = Depends(verify_api_key)
):
    """
    List all consent records.
    """
    try:
        # Get requester information
        requester_id = request.headers.get("X-User-ID", "system")
        client_ip = request.client.host if request.client else "unknown"
        
        # Get all consents
        results = consent_manager.get_all_consents(active_only=active_only)
        
        # Log access to consent list
        audit_logger.log_event(
            user_id=requester_id,
            action="api_list_consents",
            resource="employee/consent",
            details={
                "ip_address": client_ip,
                "user_agent": request.headers.get("User-Agent", "unknown"),
                "active_only": active_only,
                "count": len(results)
            }
        )
        
        # Add status to each result
        for result in results:
            result["status"] = "success"
        
        return results
    except Exception as e:
        logger.error(f"Error listing consents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list consents: {str(e)}")

# Audit log endpoints
@router.post("/audit-logs", response_model=List[Dict[str, Any]])
async def get_audit_logs(
    request: Request,
    log_request: AuditLogRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Get audit logs based on filter criteria.
    """
    try:
        # Get requester information
        requester_id = request.headers.get("X-User-ID", "system")
        client_ip = request.client.host if request.client else "unknown"
        
        # Get logs
        logs = audit_logger.get_logs(
            start_date=log_request.start_date,
            end_date=log_request.end_date,
            user_id=log_request.user_id,
            action=log_request.action,
            limit=log_request.limit
        )
        
        # Log access to audit logs
        audit_logger.log_event(
            user_id=requester_id,
            action="api_get_audit_logs",
            resource="audit_logs",
            details={
                "ip_address": client_ip,
                "user_agent": request.headers.get("User-Agent", "unknown"),
                "filters": log_request.dict(),
                "results_count": len(logs)
            }
        )
        
        return logs
    except Exception as e:
        logger.error(f"Error getting audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")

@router.post("/apply-retention")
async def apply_retention_policy(
    request: Request,
    api_key: str = Depends(verify_api_key)
):
    """
    Apply retention policy to consent records and audit logs.
    """
    try:
        # Get requester information
        requester_id = request.headers.get("X-User-ID", "system")
        client_ip = request.client.host if request.client else "unknown"
        
        # Apply retention policies
        consent_deleted = consent_manager.apply_retention_policy()
        logs_deleted = audit_logger.cleanup_old_logs()
        
        # Log retention policy application
        audit_logger.log_event(
            user_id=requester_id,
            action="apply_retention_policy",
            resource="system",
            details={
                "ip_address": client_ip,
                "user_agent": request.headers.get("User-Agent", "unknown"),
                "consent_records_deleted": consent_deleted,
                "log_files_deleted": logs_deleted
            }
        )
        
        return {
            "status": "success",
            "consent_records_deleted": consent_deleted,
            "log_files_deleted": logs_deleted
        }
    except Exception as e:
        logger.error(f"Error applying retention policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to apply retention policy: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check endpoint for the compliance system.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "consent_manager": "operational",
            "audit_logger": "operational"
        }
    }