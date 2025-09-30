#!/usr/bin/env python3
"""
Tests for the compliance module, including consent management and audit logging.
"""

import os
import json
import unittest
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compliance.consent_manager import ConsentManager
from compliance.audit_logger import ImmutableAuditLogger


class TestConsentManager(unittest.TestCase):
    """Test cases for the ConsentManager class."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.consent_file = os.path.join(self.temp_dir, "consent_data.json")
        self.consent_manager = ConsentManager(consent_file=self.consent_file)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_set_consent(self):
        """Test setting consent preferences."""
        # Set consent for a user
        result = self.consent_manager.set_consent(
            employee_id="emp123",
            monitoring_enabled=True,
            data_retention_days=90,
            allow_analytics=True
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["employee_id"], "emp123")
        
        # Verify consent was saved
        with open(self.consent_file, 'r') as f:
            consent_data = json.load(f)
        
        self.assertIn("emp123", consent_data)
        self.assertTrue(consent_data["emp123"]["monitoring_enabled"])
        self.assertEqual(consent_data["emp123"]["data_retention_days"], 90)
        self.assertTrue(consent_data["emp123"]["allow_analytics"])

    def test_get_consent(self):
        """Test retrieving consent preferences."""
        # Set consent first
        self.consent_manager.set_consent(
            employee_id="emp456",
            monitoring_enabled=False,
            data_retention_days=30,
            allow_analytics=False
        )
        
        # Get consent
        consent = self.consent_manager.get_consent("emp456")
        
        self.assertEqual(consent["employee_id"], "emp456")
        self.assertFalse(consent["monitoring_enabled"])
        self.assertEqual(consent["data_retention_days"], 30)
        self.assertFalse(consent["allow_analytics"])
        
        # Test getting non-existent consent
        consent = self.consent_manager.get_consent("nonexistent")
        self.assertIsNone(consent)

    def test_list_consents(self):
        """Test listing all consent preferences."""
        # Set consent for multiple users
        self.consent_manager.set_consent(
            employee_id="emp1",
            monitoring_enabled=True,
            data_retention_days=90
        )
        
        self.consent_manager.set_consent(
            employee_id="emp2",
            monitoring_enabled=False,
            data_retention_days=30
        )
        
        # List all consents
        consents = self.consent_manager.list_consents()
        
        self.assertEqual(len(consents), 2)
        self.assertIn("emp1", [c["employee_id"] for c in consents])
        self.assertIn("emp2", [c["employee_id"] for c in consents])

    def test_apply_retention_policy(self):
        """Test applying retention policy."""
        # Create a mock audit logger
        mock_logger = MagicMock()
        
        # Set consent with different retention periods
        self.consent_manager.set_consent(
            employee_id="emp1",
            monitoring_enabled=True,
            data_retention_days=90
        )
        
        self.consent_manager.set_consent(
            employee_id="emp2",
            monitoring_enabled=True,
            data_retention_days=30
        )
        
        # Apply retention policy
        result = self.consent_manager.apply_retention_policy(mock_logger)
        
        # Verify audit logger was called with correct retention periods
        mock_logger.apply_retention_policy.assert_called()
        calls = mock_logger.apply_retention_policy.call_args_list
        
        # Check that both retention policies were applied
        retention_days = [call[0][1] for call in calls]
        self.assertIn(90, retention_days)
        self.assertIn(30, retention_days)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["policies_applied"], 2)


class TestAuditLogger(unittest.TestCase):
    """Test cases for the ImmutableAuditLogger class."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = os.path.join(self.temp_dir, "audit_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.audit_logger = ImmutableAuditLogger(log_dir=self.log_dir)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_log_event(self):
        """Test logging an event."""
        # Log an event
        event_id = self.audit_logger.log_event(
            user_id="user123",
            action="data_access",
            resource="customer_data",
            status="success",
            details={"query": "SELECT * FROM customers"}
        )
        
        self.assertIsNotNone(event_id)
        
        # Verify log file was created
        log_files = os.listdir(self.log_dir)
        self.assertEqual(len(log_files), 1)
        
        # Read log file and verify content
        log_file_path = os.path.join(self.log_dir, log_files[0])
        with open(log_file_path, 'r') as f:
            log_entries = [json.loads(line) for line in f]
        
        self.assertEqual(len(log_entries), 1)
        log_entry = log_entries[0]
        
        self.assertEqual(log_entry["user_id"], "user123")
        self.assertEqual(log_entry["action"], "data_access")
        self.assertEqual(log_entry["resource"], "customer_data")
        self.assertEqual(log_entry["status"], "success")
        self.assertEqual(log_entry["details"]["query"], "SELECT * FROM customers")
        self.assertEqual(log_entry["event_id"], event_id)

    def test_get_logs(self):
        """Test retrieving logs."""
        # Log multiple events
        self.audit_logger.log_event(
            user_id="user1",
            action="login",
            resource="system",
            status="success"
        )
        
        self.audit_logger.log_event(
            user_id="user2",
            action="data_access",
            resource="customer_data",
            status="denied"
        )
        
        self.audit_logger.log_event(
            user_id="user1",
            action="logout",
            resource="system",
            status="success"
        )
        
        # Get all logs
        logs = self.audit_logger.get_logs()
        self.assertEqual(len(logs), 3)
        
        # Filter logs by user_id
        user1_logs = self.audit_logger.get_logs(filters={"user_id": "user1"})
        self.assertEqual(len(user1_logs), 2)
        self.assertEqual(user1_logs[0]["user_id"], "user1")
        self.assertEqual(user1_logs[1]["user_id"], "user1")
        
        # Filter logs by action
        login_logs = self.audit_logger.get_logs(filters={"action": "login"})
        self.assertEqual(len(login_logs), 1)
        self.assertEqual(login_logs[0]["action"], "login")

    def test_apply_retention_policy(self):
        """Test applying retention policy to logs."""
        # Create a log file with old timestamp
        old_date = datetime.now() - timedelta(days=100)
        old_log_file = self.audit_logger._generate_log_filename(old_date)
        old_log_path = os.path.join(self.log_dir, old_log_file)
        
        with open(old_log_path, 'w') as f:
            f.write(json.dumps({
                "event_id": "old_event",
                "timestamp": old_date.isoformat(),
                "user_id": "user1",
                "action": "old_action",
                "resource": "old_resource",
                "status": "success"
            }) + "\n")
        
        # Create a recent log file
        recent_date = datetime.now() - timedelta(days=10)
        recent_log_file = self.audit_logger._generate_log_filename(recent_date)
        recent_log_path = os.path.join(self.log_dir, recent_log_file)
        
        with open(recent_log_path, 'w') as f:
            f.write(json.dumps({
                "event_id": "recent_event",
                "timestamp": recent_date.isoformat(),
                "user_id": "user2",
                "action": "recent_action",
                "resource": "recent_resource",
                "status": "success"
            }) + "\n")
        
        # Apply retention policy (30 days)
        result = self.audit_logger.apply_retention_policy(retention_days=30)
        
        # Verify old log was deleted but recent log remains
        self.assertTrue(result["success"])
        self.assertEqual(result["logs_deleted"], 1)
        self.assertFalse(os.path.exists(old_log_path))
        self.assertTrue(os.path.exists(recent_log_path))


class TestAPIIntegration(unittest.TestCase):
    """Test cases for API integration."""
    
    @patch('compliance.api.ConsentManager')
    @patch('compliance.api.ImmutableAuditLogger')
    def test_api_integration(self, mock_logger_class, mock_consent_class):
        """Test API integration with mocked dependencies."""
        # This is a placeholder for API integration tests
        # In a real implementation, you would use FastAPI's TestClient
        # to test the API endpoints
        
        # Mock the consent manager
        mock_consent_manager = MagicMock()
        mock_consent_class.return_value = mock_consent_manager
        mock_consent_manager.get_consent.return_value = {
            "employee_id": "emp123",
            "monitoring_enabled": True,
            "data_retention_days": 90,
            "allow_analytics": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # Mock the audit logger
        mock_logger = MagicMock()
        mock_logger_class.return_value = mock_logger
        mock_logger.log_event.return_value = "test_event_id"
        
        # Import the API module (which will use our mocks)
        from compliance import api
        
        # Verify that the router was created
        self.assertIsNotNone(api.router)
        
        # Note: In a real test, you would use FastAPI's TestClient to test the endpoints
        # For example:
        # from fastapi.testclient import TestClient
        # client = TestClient(app)
        # response = client.post("/compliance/consent", json={"employee_id": "emp123", ...})
        # self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()