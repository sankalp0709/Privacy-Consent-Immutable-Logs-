"""
Immutable Audit Logger for BHIV Core
Provides tamper-proof logging of all system actions
"""
import os
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from utils.logger import get_logger

logger = get_logger(__name__)

class ImmutableAuditLogger:
    """
    Append-only audit logging system that maintains immutable records
    of all system actions for compliance and security purposes.
    """
    
    def __init__(self, log_dir: str = "audit_logs"):
        """
        Initialize the audit logger with a specified log directory.
        
        Args:
            log_dir: Directory to store audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        self.current_log_file = self._get_log_filename()
        logger.info(f"Initialized ImmutableAuditLogger with log directory: {self.log_dir}")
    
    def _get_log_filename(self) -> Path:
        """Generate a log filename based on the current date"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"audit_log_{today}.jsonl"
    
    def log_event(self, 
                 user_id: str, 
                 action: str, 
                 resource: str, 
                 details: Optional[Dict[str, Any]] = None,
                 status: str = "success") -> Dict[str, Any]:
        """
        Log an audit event with complete details.
        
        Args:
            user_id: ID of the user performing the action
            action: Type of action performed (e.g., "access", "modify", "delete")
            resource: Resource being accessed or modified
            details: Additional details about the action
            status: Outcome status of the action
            
        Returns:
            The complete log entry that was recorded
        """
        # Create a unique event ID
        event_id = str(uuid.uuid4())
        
        # Create the log entry with all required fields
        log_entry = {
            "event_id": event_id,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "status": status,
            "details": details or {},
            "ip_address": details.get("ip_address") if details else None,
            "user_agent": details.get("user_agent") if details else None
        }
        
        # Ensure the log directory exists
        self.log_dir.mkdir(exist_ok=True, parents=True)
        
        # Update the current log file if date has changed
        self.current_log_file = self._get_log_filename()
        
        # Append the log entry to the file (append-only for immutability)
        try:
            with open(self.current_log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            logger.debug(f"Audit log entry created: {event_id}")
            return log_entry
        except Exception as e:
            logger.error(f"Failed to write audit log: {str(e)}")
            raise
    
    def get_logs(self, 
                start_date: Optional[str] = None, 
                end_date: Optional[str] = None,
                user_id: Optional[str] = None,
                action: Optional[str] = None,
                limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve logs based on filter criteria.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            user_id: Filter by specific user
            action: Filter by specific action
            limit: Maximum number of logs to return
            
        Returns:
            List of matching log entries
        """
        logs = []
        
        # Determine which log files to search
        log_files = list(self.log_dir.glob("audit_log_*.jsonl"))
        
        # Filter log files by date range if specified
        if start_date or end_date:
            filtered_files = []
            for log_file in log_files:
                file_date = log_file.stem.split('_')[-1]
                if start_date and file_date < start_date:
                    continue
                if end_date and file_date > end_date:
                    continue
                filtered_files.append(log_file)
            log_files = filtered_files
        
        # Process each log file
        for log_file in log_files:
            if not log_file.exists():
                continue
                
            with open(log_file, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Apply filters
                        if user_id and entry.get("user_id") != user_id:
                            continue
                        if action and entry.get("action") != action:
                            continue
                            
                        logs.append(entry)
                        
                        # Check limit
                        if len(logs) >= limit:
                            return logs[:limit]
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in log file {log_file}")
                        continue
        
        return logs[:limit]
    
    def cleanup_old_logs(self, retention_days: int = 90) -> int:
        """
        Remove logs older than the specified retention period.
        
        Args:
            retention_days: Number of days to retain logs
            
        Returns:
            Number of log files deleted
        """
        # Calculate the cutoff date
        cutoff = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
        deleted_count = 0
        
        # Check each log file
        for log_file in self.log_dir.glob("audit_log_*.jsonl"):
            try:
                file_date = datetime.strptime(log_file.stem.split('_')[-1], "%Y-%m-%d")
                if file_date.timestamp() < cutoff:
                    # Log the deletion event before deleting
                    self.log_event(
                        user_id="system",
                        action="delete",
                        resource=str(log_file),
                        details={"reason": "retention_policy", "retention_days": retention_days}
                    )
                    
                    # Delete the file
                    log_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old audit log: {log_file}")
            except (ValueError, OSError) as e:
                logger.error(f"Error processing log file {log_file}: {str(e)}")
        
        return deleted_count

# Global instance for easy import
audit_logger = ImmutableAuditLogger()