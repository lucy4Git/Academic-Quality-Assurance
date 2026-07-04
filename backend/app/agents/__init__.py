"""AQAA AI audit agent package.

Each agent is a pure-function module (no SQLAlchemy, no HTTP) that takes
a structured snapshot of evidence data and returns a structured result.
The service layer (services/audit_service.py) handles all DB I/O and
calls the relevant agent function.

Agents implemented so far:
    module_folder_audit — checks whether all required QA documents are present.
"""
