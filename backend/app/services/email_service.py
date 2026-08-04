"""Email service — console/log mode by default, SMTP optional.

If SMTP is not configured (SMTP_HOST is empty or unset), all emails are
printed to the application logger at INFO level.  This allows the full
registration flow to work in development without any mail server.

To enable real email delivery, set in backend/.env:
    SMTP_HOST=smtp.yourdomain.ac.za
    SMTP_PORT=587
    SMTP_USERNAME=noreply@yourdomain.ac.za
    SMTP_PASSWORD=<password>
    SMTP_FROM=noreply@yourdomain.ac.za
    SMTP_TLS=true
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def _smtp_configured() -> bool:
    host = getattr(settings, "SMTP_HOST", None)
    return bool(host and host.strip())


def send_email(to: str, subject: str, body_text: str, body_html: str | None = None) -> None:
    """Send an email or log it to console if SMTP is not configured."""
    if not _smtp_configured():
        logger.info(
            "[EMAIL — CONSOLE MODE] To: %s | Subject: %s\n%s",
            to,
            subject,
            body_text,
        )
        return

    host = settings.SMTP_HOST  # type: ignore[attr-defined]
    port = getattr(settings, "SMTP_PORT", 587)
    username = getattr(settings, "SMTP_USERNAME", "")
    password = getattr(settings, "SMTP_PASSWORD", "")
    from_addr = getattr(settings, "SMTP_FROM", username)
    use_tls = getattr(settings, "SMTP_TLS", True)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to
    msg.attach(MIMEText(body_text, "plain"))
    if body_html:
        msg.attach(MIMEText(body_html, "html"))

    try:
        if use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port) as server:
                server.starttls(context=context)
                if username:
                    server.login(username, password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port) as server:
                if username:
                    server.login(username, password)
                server.send_message(msg)
        logger.info("Email sent to %s: %s", to, subject)
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to, exc)


def send_verification_email(to: str, full_name: str, code: str) -> None:
    """Send an email verification code to a newly registered user."""
    subject = "AQAA — Verify your email address"
    body_text = (
        f"Hello {full_name},\n\n"
        f"Your AQAA email verification code is:\n\n"
        f"    {code}\n\n"
        f"This code expires in 24 hours.\n\n"
        f"Enter this code on the verification page to activate your account.\n\n"
        f"If you did not register for AQAA, please ignore this email.\n\n"
        f"— AQAA Academic Quality Assurance Agent"
    )
    body_html = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
      <div style="background: #1e40af; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
        <h2 style="margin:0">AQAA — Email Verification</h2>
      </div>
      <div style="border: 1px solid #e5e7eb; border-top: none; padding: 24px; border-radius: 0 0 8px 8px;">
        <p>Hello <strong>{full_name}</strong>,</p>
        <p>Your email verification code is:</p>
        <div style="background: #f3f4f6; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0;">
          <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #1e40af;">{code}</span>
        </div>
        <p style="color: #6b7280; font-size: 14px;">This code expires in 24 hours.</p>
        <p style="color: #6b7280; font-size: 14px;">If you did not register for AQAA, please ignore this email.</p>
      </div>
    </div>
    """
    send_email(to, subject, body_text, body_html)


def send_activation_email(to: str, full_name: str, raw_token: str) -> None:
    """Send an activation link containing the one-time token."""
    frontend_base = settings.FRONTEND_BASE_URL
    activation_url = f"{frontend_base}/activate?token={raw_token}"
    subject = "AQAA — Activate your account"
    body_text = (
        f"Hello {full_name},\n\n"
        f"Your AQAA account registration has been approved.\n\n"
        f"Click the link below to set your password and activate your account:\n\n"
        f"    {activation_url}\n\n"
        f"This link expires in 48 hours and can only be used once.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"— AQAA Academic Quality Assurance Agent"
    )
    body_html = f"""
    <div style="font-family: sans-serif; max-width: 520px; margin: 0 auto; padding: 24px;">
      <div style="background: #1e40af; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
        <h2 style="margin:0">AQAA — Account Approved</h2>
      </div>
      <div style="border: 1px solid #e5e7eb; border-top: none; padding: 24px; border-radius: 0 0 8px 8px;">
        <p>Hello <strong>{full_name}</strong>,</p>
        <p>Your account registration has been approved. Click the button below to set your password and activate your account.</p>
        <div style="text-align: center; margin: 28px 0;">
          <a href="{activation_url}" style="background:#1e40af;color:white;padding:14px 28px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:16px;">Activate My Account</a>
        </div>
        <p style="color: #6b7280; font-size: 13px;">Or copy this link into your browser:<br>{activation_url}</p>
        <p style="color: #6b7280; font-size: 13px;">This link expires in 48 hours and can only be used once.</p>
      </div>
    </div>
    """
    send_email(to, subject, body_text, body_html)


def send_rejection_email(to: str, full_name: str, reason: str | None = None) -> None:
    """Notify a user that their registration was rejected."""
    subject = "AQAA — Account registration update"
    reason_line = f"Reason: {reason}\n\n" if reason else ""
    body_text = (
        f"Hello {full_name},\n\n"
        f"Your AQAA account registration was not approved at this time.\n\n"
        f"{reason_line}"
        f"Please contact your institution's QA office if you believe this is an error.\n\n"
        f"— AQAA Academic Quality Assurance Agent"
    )
    send_email(to, subject, body_text)


def send_approval_notification(to: str, full_name: str, approved: bool, reason: str | None = None) -> None:
    """Notify a user that their account has been approved or rejected."""
    if approved:
        subject = "AQAA — Your account has been approved"
        body_text = (
            f"Hello {full_name},\n\n"
            f"Your AQAA account has been approved. You can now sign in at the platform.\n\n"
            f"— AQAA Academic Quality Assurance Agent"
        )
    else:
        subject = "AQAA — Account registration update"
        body_text = (
            f"Hello {full_name},\n\n"
            f"Your AQAA account registration was not approved at this time.\n"
            + (f"Reason: {reason}\n\n" if reason else "\n")
            + f"Please contact your institution's QA office if you believe this is an error.\n\n"
            f"— AQAA Academic Quality Assurance Agent"
        )
    send_email(to, subject, body_text)
