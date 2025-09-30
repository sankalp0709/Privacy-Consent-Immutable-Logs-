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
    
    def __init__(self, storage_path: str = "data/consent"):
        """
        Initialize the consent manager with a specified storage location.
        
        Args:
            storage_path: Directory to store consent data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True, parents=True)
        self.default_retention_days = 90  # Default retention period in days
        logger.info(f"Initialized ConsentManager with storage path: {self.storage_path}")
    
    def set_consent(self, 
                   employee_id: str, 
                   monitoring_enabled: bool,
                   retention_days: Optional[int] = None,
                   data_categories: Optional[List[str]] = None,
                   requester_id: str = "system") -> Dict[str, Any]:
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
        retention = retention_days or self.default_retention_days
        expiration_date = (datetime.now() + timedelta(days=retention)).isoformat()
        
        # Create or update consent record
        consent_data = {
            "employee_id": employee_id,
            "monitoring_enabled": monitoring_enabled,
            "retention_days": retention,
            "expiration_date": expiration_date,
            "data_categories": data_categories or ["all"],
            "last_updated": datetime.now().isoformat(),
            "last_updated_by": requester_id
        }
        
        # Save to file
        consent_file = self.storage_path / f"{employee_id}.json"
        with open(consent_file, "w") as f:
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
        return consent_data
    
    def get_consent(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """
        Get consent preferences for a user.
        
        Args:
            employee_id: ID of the employee
            
        Returns:
            The consent settings or None if not found
        """
        consent_file = self.storage_path / f"{employee_id}.json"
        
        if not consent_file.exists():
            logger.debug(f"No consent record found for employee {employee_id}")
            return None
        
        try:
            with open(consent_file, "r") as f:
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
    
    def apply_retention_policy(self) -> int:
        """
        Apply retention policy to all consent records.
        Removes expired consent records.
        
        Returns:
            Number of records deleted
        """
        deleted_count = 0
        
        for consent_file in self.storage_path.glob("*.json"):
            try:
                with open(consent_file, "r") as f:
                    consent_data = json.load(f)
                
                # Check if consent has expired
                expiration_date = datetime.fromisoformat(consent_data.get("expiration_date", ""))
                if datetime.now() > expiration_date:
                    # Log the deletion
                    employee_id = consent_file.stem
                    audit_logger.log_event(
                        user_id="system",
                        action="delete_consent",
                        resource=f"employee/{employee_id}/consent",
                        details={"reason": "retention_policy_expired"}
                    )
                    
                    # Delete the file
                    consent_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted expired consent record for {employee_id}")
            except Exception as e:
                logger.error(f"Error processing consent file {consent_file}: {str(e)}")
        
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
        
        for consent_file in self.storage_path.glob("*.json"):
            try:
                with open(consent_file, "r") as f:
                    consent_data = json.load(f)
                
                # Filter expired consents if active_only is True
                if active_only:
                    try:
                        expiration_date = datetime.fromisoformat(consent_data.get("expiration_date", ""))
                        if datetime.now() > expiration_date:
                            continue
                    except (ValueError, TypeError):
                        # Include records with invalid expiration dates when listing all
                        if active_only:
                            continue
                
                consents.append(consent_data)
            except Exception as e:
                logger.error(f"Error reading consent file {consent_file}: {str(e)}")
        
        return consents

# Global instance for easy import
consent_manager = ConsentManager()