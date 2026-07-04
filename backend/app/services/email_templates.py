"""Email notification templates for AQAA.

These functions return (subject, html_body) tuples. No SMTP is configured —
templates are available for future integration with an email delivery service.
"""

from __future__ import annotations

from datetime import datetime


def _base(title: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>{title}</title></head>
<body style="font-family:Arial,sans-serif;color:#1a1a1a;max-width:600px;margin:0 auto;padding:24px;">
  <div style="border-bottom:3px solid #2563eb;padding-bottom:16px;margin-bottom:24px;">
    <h2 style="color:#2563eb;margin:0;">AQAA — Academic Quality Assurance</h2>
  </div>
  {body_html}
  <div style="margin-top:32px;padding-top:16px;border-top:1px solid #e5e7eb;font-size:12px;color:#6b7280;">
    <p>This is an automated notification from AQAA. Do not reply to this email.</p>
  </div>
</body>
</html>""".strip()


def audit_assigned(
    assignee_name: str,
    audit_id: str,
    module_code: str,
    due_date: "datetime | None",
    priority: "str | None",
) -> "tuple[str, str]":
    due = due_date.strftime("%d %B %Y") if due_date else "Not specified"
    pri = priority.upper() if priority else "Not specified"
    body = (
        f"<h3>An audit has been assigned to you</h3>"
        f"<p>Hello {assignee_name},</p>"
        f"<p>Module: <strong>{module_code}</strong> | Due: <strong>{due}</strong> | Priority: <strong>{pri}</strong></p>"
        f"<p style='font-size:12px;color:#6b7280;'>Audit ID: {audit_id}</p>"
    )
    return "Audit Assigned — Action Required", _base("Audit Assigned", body)


def audit_approved(assignee_name: str, audit_id: str, module_code: str) -> "tuple[str, str]":
    body = (
        f"<h3 style='color:#16a34a;'>Audit Approved</h3>"
        f"<p>Hello {assignee_name}, your audit for <strong>{module_code}</strong> has been approved.</p>"
        f"<p style='font-size:12px;color:#6b7280;'>Audit ID: {audit_id}</p>"
    )
    return f"Audit Approved — {module_code}", _base("Audit Approved", body)


def audit_rejected(
    assignee_name: str,
    audit_id: str,
    module_code: str,
    remarks: "str | None",
) -> "tuple[str, str]":
    remarks_html = f"<p><strong>Remarks:</strong> {remarks}</p>" if remarks else ""
    body = (
        f"<h3 style='color:#dc2626;'>Audit Rejected</h3>"
        f"<p>Hello {assignee_name}, your audit for <strong>{module_code}</strong> has been rejected.</p>"
        f"{remarks_html}"
        f"<p style='font-size:12px;color:#6b7280;'>Audit ID: {audit_id}</p>"
    )
    return f"Audit Rejected — {module_code}", _base("Audit Rejected", body)


def audit_returned(
    assignee_name: str,
    audit_id: str,
    module_code: str,
    remarks: "str | None",
) -> "tuple[str, str]":
    remarks_html = f"<p><strong>Feedback:</strong> {remarks}</p>" if remarks else ""
    body = (
        f"<h3 style='color:#d97706;'>Audit Returned for Corrections</h3>"
        f"<p>Hello {assignee_name}, your audit for <strong>{module_code}</strong> was returned for corrections.</p>"
        f"{remarks_html}"
        f"<p style='font-size:12px;color:#6b7280;'>Audit ID: {audit_id}</p>"
    )
    return f"Audit Returned for Corrections — {module_code}", _base("Audit Returned", body)


def new_comment(
    recipient_name: str,
    audit_id: str,
    commenter_name: str,
    comment_excerpt: str,
) -> "tuple[str, str]":
    body = (
        f"<h3>New Comment on Your Audit</h3>"
        f"<p>Hello {recipient_name}, <strong>{commenter_name}</strong> commented:</p>"
        f"<blockquote style='border-left:4px solid #2563eb;margin:16px 0;padding:8px 16px;font-style:italic;'>{comment_excerpt}</blockquote>"
        f"<p style='font-size:12px;color:#6b7280;'>Audit ID: {audit_id}</p>"
    )
    return "New Comment on Audit", _base("New Comment", body)
