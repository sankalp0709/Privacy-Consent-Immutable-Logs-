"""
Consent Manager for BHIV Core
Handles user consent preferences and privacy controls
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from utils.logger import get_logger
from compliance.audit_logger import audit_logger

logger = get_logger(__name__)

class ConsentManager:
    """
    Manages user consent preferences and privacy controls.
    Provides functionality to store, retrieve, and enforce consent settings.
    """
    
    def __init__(self, storage_path: str = "data/consent", consent_file: Optional[str] = None):
        """
        Initialize the consent manager with a specified storage location.
        
        Args:
            storage_path: Directory to store consent data
            consent_file: Optional path to a single JSON file for all consents
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True, parents=True)
        self.consent_file = Path(consent_file) if consent_file else None
        if self.consent_file:
            self.consent_file.parent.mkdir(exist_ok=True, parents=True)
            if not self.consent_file.exists():
                with open(self.consent_file, "w") as f:
                    json.dump({}, f)
        self.default_retention_days = 90  # Default retention period in days
        logger.info(f"Initialized ConsentManager with storage path: {self.storage_path}")
    
    def set_consent(self, 
                   employee_id: str, 
                   monitoring_enabled: bool,
                   retention_days: Optional[int] = None,
                   data_categories: Optional[List[str]] = None,
                   requester_id: str = "system",
                   # Backward-compatible parameters used in legacy tests
                   data_retention_days: Optional[int] = None,
                   allow_analytics: Optional[bool] = None) -> Dict[str, Any]:
        """
        Set consent preferences for a user.
        
        Args:
            employee_id: ID of the employee
            monitoring_enabled: Whether monitoring is enabled for this employee
            retention_days: Custom retention period in days (overrides default)
            data_categories: Specific data categories consent applies to
            requester_id: ID of the user making the change
            
        Returns:
            The updated consent settings
        """
        # Calculate expiration date based on retention period
        # Prefer legacy test param if provided, otherwise use new param, else default
        retention = (
            data_retention_days if data_retention_days is not None else
            (retention_days if retention_days is not None else self.default_retention_days)
        )
        expiration_date = (datetime.now() + timedelta(days=retention)).isoformat()
        
        # Create or update consent record
        consent_data = {
            "employee_id": employee_id,
            "monitoring_enabled": monitoring_enabled,
            "retention_days": retention,
            # Legacy fields for tests / backward compatibility
            "data_retention_days": retention,
            "allow_analytics": bool(allow_analytics) if allow_analytics is not None else True,
            "expiration_date": expiration_date,
            "data_categories": data_categories or ["all"],
            "last_updated": datetime.now().isoformat(),
            "last_updated_by": requester_id
        }
        
        # Save to file (directory mode or single-file mode)
        if self.consent_file:
            try:
                with open(self.consent_file, "r") as f:
                    all_data = json.load(f)
            except Exception:
                all_data = {}
            all_data[employee_id] = consent_data
            with open(self.consent_file, "w") as f:
                json.dump(all_data, f, indent=2)
        else:
            consent_path = self.storage_path / f"{employee_id}.json"
            with open(consent_path, "w") as f:
                json.dump(consent_data, f, indent=2)
        
        # Log the consent change in audit log
        audit_logger.log_event(
            user_id=requester_id,
            action="set_consent",
            resource=f"employee/{employee_id}/consent",
            details={
                "monitoring_enabled": monitoring_enabled,
                "retention_days": retention,
                "data_categories": data_categories or ["all"]
            }
        )
        
        logger.info(f"Updated consent settings for employee {employee_id}: monitoring_enabled={monitoring_enabled}")
        # Return with success flag for legacy tests
        return {**consent_data, "success": True}

    # Legacy alias for tests
    def list_consents(self) -> List[Dict[str, Any]]:
        return self.get_all_consents(active_only=False)
    
    def get_consent(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """
        Get consent preferences for a user.
        
        Args:
            employee_id: ID of the employee
            
        Returns:
            The consent settings or None if not found
        """
        try:
            if self.consent_file:
                with open(self.consent_file, "r") as f:
                    all_data = json.load(f)
                consent_data = all_data.get(employee_id)
                if consent_data is None:
                    logger.debug(f"No consent record found for employee {employee_id}")
                    return None
            else:
                consent_path = self.storage_path / f"{employee_id}.json"
                if not consent_path.exists():
                    logger.debug(f"No consent record found for employee {employee_id}")
                    return None
                with open(consent_path, "r") as f:
                    consent_data = json.load(f)
            # Log the consent access in audit log
            audit_logger.log_event(
                user_id="system",
                action="access_consent",
                resource=f"employee/{employee_id}/consent",
                details={"access_type": "read"}
            )
            return consent_data
        except Exception as e:
            logger.error(f"Error reading consent data for {employee_id}: {str(e)}")
            return None
    
    def is_monitoring_allowed(self, employee_id: str) -> bool:
        """
        Check if monitoring is allowed for a specific employee.
        
        Args:
            employee_id: ID of the employee
            
        Returns:
            True if monitoring is allowed, False otherwise
        """
        consent = self.get_consent(employee_id)
        
        # Default to False if no consent record exists
        if not consent:
            return False
        
        # Check if consent has expired
        try:
            expiration_date = datetime.fromisoformat(consent.get("expiration_date", ""))
            if datetime.now() > expiration_date:
                logger.warning(f"Consent for employee {employee_id} has expired")
                return False
        except (ValueError, TypeError):
            logger.error(f"Invalid expiration date format for employee {employee_id}")
            return False
        
        return consent.get("monitoring_enabled", False)
    
    def apply_retention_policy(self, external_logger: Optional[Any] = None) -> Any:
        """
        Apply retention policy to all consent records.
        Removes expired consent records.
        
        Returns:
            If external_logger provided: dict with success and policies_applied
            Else: number of records deleted
        """
        deleted_count = 0
        policies_applied = 0
        
        if self.consent_file:
            try:
                with open(self.consent_file, "r") as f:
                    all_data = json.load(f)
            except Exception:
                all_data = {}
            for employee_id, consent_data in list(all_data.items()):
                try:
                    expiration_date = datetime.fromisoformat(consent_data.get("expiration_date", ""))
                    if datetime.now() > expiration_date:
                        audit_logger.log_event(
                            user_id="system",
                            action="delete_consent",
                            resource=f"employee/{employee_id}/consent",
                            details={"reason": "retention_policy_expired"}
                        )
                        all_data.pop(employee_id, None)
                        with open(self.consent_file, "w") as f:
                            json.dump(all_data, f, indent=2)
                        deleted_count += 1
                        logger.info(f"Deleted expired consent record for {employee_id}")
                    if external_logger is not None:
                        retention_days = consent_data.get("data_retention_days") or consent_data.get("retention_days", self.default_retention_days)
                        try:
                            external_logger.apply_retention_policy(employee_id, retention_days)
                            policies_applied += 1
                        except Exception as e:
                            logger.warning(f"External logger retention failed for {employee_id}: {e}")
                except Exception as e:
                    logger.error(f"Error processing consent record for {employee_id}: {e}")
        else:
            for consent_path in self.storage_path.glob("*.json"):
                try:
                    with open(consent_path, "r") as f:
                        consent_data = json.load(f)
                    # Check if consent has expired
                    expiration_date = datetime.fromisoformat(consent_data.get("expiration_date", ""))
                    if datetime.now() > expiration_date:
                        # Log the deletion
                        employee_id = consent_path.stem
                        audit_logger.log_event(
                            user_id="system",
                            action="delete_consent",
                            resource=f"employee/{employee_id}/consent",
                            details={"reason": "retention_policy_expired"}
                        )
                        # Delete the file
                        consent_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted expired consent record for {employee_id}")
                    # If an external logger is provided, apply its retention policy per record
                    if external_logger is not None:
                        employee_id = consent_path.stem
                        retention_days = consent_data.get("data_retention_days") or consent_data.get("retention_days", self.default_retention_days)
                        try:
                            # Call signature expected by tests: (employee_id, retention_days)
                            external_logger.apply_retention_policy(employee_id, retention_days)
                            policies_applied += 1
                        except Exception as e:
                            logger.warning(f"External logger retention failed for {employee_id}: {e}")
                except Exception as e:
                    logger.error(f"Error processing consent file {consent_path}: {str(e)}")
        
        if external_logger is not None:
            return {"success": True, "policies_applied": policies_applied}
        return deleted_count
    
    def get_all_consents(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all consent records.
        
        Args:
            active_only: If True, only return non-expired consents
            
        Returns:
            List of consent records
        """
        consents = []

        # Single-file consent storage mode
        if self.consent_file:
            try:
                with open(self.consent_file, "r") as f:
                    all_data = json.load(f)
            except Exception:
                all_data = {}
            for _, consent_data in all_data.items():
                try:
                    if active_only:
                        expiration_date = datetime.fromisoformat(consent_data.get("expiration_date", ""))
                        if datetime.now() > expiration_date:
                            continue
                except (ValueError, TypeError):
                    if active_only:
                        continue
                consents.append(consent_data)
            return consents

        # Directory-based consent storage mode
        for consent_path in self.storage_path.glob("*.json"):
            try:
                with open(consent_path, "r") as f:
                    consent_data = json.load(f)
                if active_only:
                    try:
                        expiration_date = datetime.fromisoformat(consent_data.get("expiration_date", ""))
                        if datetime.now() > expiration_date:
                            continue
                    except (ValueError, TypeError):
                        if active_only:
                            continue
                consents.append(consent_data)
            except Exception as e:
                logger.error(f"Error reading consent file {consent_path}: {str(e)}")

        return consents

# Global instance for easy import
consent_manager = ConsentManager()