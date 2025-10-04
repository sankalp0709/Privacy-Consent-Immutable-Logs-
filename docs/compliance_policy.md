# BHIV Core Compliance & Privacy Policy

## Overview

This document outlines the privacy, consent, and data retention policies implemented in the BHIV Core AI Agent System. Our compliance framework is designed to meet GDPR requirements and other relevant privacy regulations while ensuring transparency and user control over personal data.

## 1. Data Collection & Processing

### 1.1 Types of Data Collected

The BHIV Core system may collect and process the following types of data:

- **User Identifiers**: Employee IDs, user IDs, or other identifiers used to associate actions with specific users
- **Query Content**: Text or multi-modal content submitted to the AI system
- **System Interactions**: Records of interactions with the AI system, including timestamps and endpoints accessed
- **Consent Preferences**: User-specified privacy and monitoring preferences
- **Audit Logs**: Records of system access, data processing activities, and administrative actions

### 1.2 Purpose of Processing

Data is processed for the following purposes:

- Providing AI-powered responses and assistance
- Improving system performance and accuracy
- Ensuring system security and preventing misuse
- Complying with legal obligations and audit requirements
- Respecting user consent preferences

## 2. Consent Management

### 2.1 Consent Framework

The BHIV Core system implements a comprehensive consent management framework:

- **Explicit Consent**: Users must provide explicit consent before their interactions are monitored or stored
- **Granular Control**: Users can specify which aspects of their data can be collected and for what purposes
- **Revocable**: Consent can be withdrawn at any time through the `/consent` API endpoint
- **Documented**: All consent actions are recorded in immutable audit logs

### 2.2 Consent API

The `/compliance/consent` API endpoint allows users to:

- Set their consent preferences
- View their current consent settings
- Update or revoke previously given consent
- Apply retention policies to their historical data

## 3. Data Retention

### 3.1 Retention Policy

The BHIV Core system implements the following data retention policies:

- **Default Retention Period**: Logs and personal data are retained for a configurable period (default: 90 days)
- **User-Controlled Deletion**: Users can request earlier deletion of their data through the consent API
- **Automatic Cleanup**: The system automatically applies retention policies to remove data that has exceeded its retention period
- **Retention Exceptions**: Certain data may be retained longer if required by law or legitimate business needs

#### 3.1.1 Implementation Details

- A daily background worker enforces retention for consent records and audit logs
- The retention window for audit logs is configurable via `AUDIT_LOG_RETENTION_DAYS` (default: `90`)
- Deletions are themselves logged as audit events, recording actor, reason, and retention window

### 3.2 Data Minimization

We follow data minimization principles:

- Only collecting data necessary for the specified purposes
- Anonymizing or pseudonymizing data where possible
- Implementing technical measures to ensure data is not kept longer than necessary

## 4. Audit Logging

### 4.1 Immutable Audit Logs

The BHIV Core system maintains tamper-proof audit logs that record:

- Who accessed what data, when, and for what purpose
- Changes to system configuration and consent settings
- Data processing activities and their outcomes
- Administrative actions and policy changes

### 4.2 Log Security

Audit logs are protected through:

- Append-only storage mechanisms (daily JSONL files)
- Cryptographic verification to detect tampering
- Access controls limiting who can view audit information
- Regular integrity checks

#### 4.2.1 Append-Only Design

- Logs are written as JSON Lines (`.jsonl`) with append-only semantics
- Each entry includes a chained SHA-256 `hash` and `prev_hash` to detect tampering
- A helper `log_access` standardizes fields: actor, action, resource, status, reason, purpose, endpoint, IP, UA
- Optional external systems can forward events to `/compliance/ems-forward` for end-to-end coverage

## 5. User Rights

Users of the BHIV Core system have the following rights:

- **Right to Access**: Users can access their personal data through appropriate API endpoints
- **Right to Rectification**: Users can correct inaccurate personal data
- **Right to Erasure**: Users can request deletion of their data (subject to legal retention requirements)
- **Right to Restrict Processing**: Users can limit how their data is used through consent settings
- **Right to Data Portability**: Users can request their data in a machine-readable format
- **Right to Object**: Users can object to certain types of processing

## 6. Security Measures

The BHIV Core system implements the following security measures to protect personal data:

- **Encryption**: Data in transit and at rest is encrypted
- **Access Controls**: Role-based access controls limit who can access different types of data
- **Authentication**: Multi-factor authentication for administrative access
- **Logging**: Comprehensive security logging and monitoring
- **Regular Testing**: Security testing and vulnerability assessments

## 7. Data Breach Procedures

In the event of a data breach, the BHIV Core system will:

- Notify affected users within 72 hours of discovery
- Document the breach in audit logs
- Implement measures to mitigate the impact
- Review and update security procedures as necessary

## 8. Compliance Contacts

For questions regarding this policy or to exercise your data rights, please contact:

- **Data Protection Officer**: [dpo@bhiv-core.example.com](mailto:dpo@bhiv-core.example.com)
- **Compliance Team**: [compliance@bhiv-core.example.com](mailto:compliance@bhiv-core.example.com)

## 9. Policy Updates

This policy may be updated periodically. All changes will be documented in the version history below and in the system's audit logs.

## Version History

- **1.1.0** - Retention worker, append-only hash chaining, EMS integration
- **1.0.0** - Initial policy