"""Email service for sending verification and password reset emails."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self):
        self.settings = get_settings()

    def _get_smtp_connection(self):
        """Create and return an SMTP connection."""
        try:
            server = smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port)
            server.starttls()
            server.login(self.settings.smtp_user, self.settings.smtp_password)
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            plain_text: Plain text fallback (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.settings.smtp_host or not self.settings.smtp_user:
            logger.warning("Email service not configured. Skipping email send.")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.settings.from_name} <{self.settings.from_email}>"
            msg["To"] = to_email

            # Attach plain text version
            if plain_text:
                msg.attach(MIMEText(plain_text, "plain", "utf-8"))

            # Attach HTML version
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            # Send email
            server = self._get_smtp_connection()
            server.sendmail(self.settings.from_email, to_email, msg.as_string())
            server.quit()

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_verification_email(
        self,
        to_email: str,
        full_name: Optional[str],
        token: str,
        frontend_url: str = "http://localhost:5173",
    ) -> bool:
        """Send email verification link."""
        verification_url = f"{frontend_url}/verify-email?token={token}"

        subject = "Verify Your Email Address"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Verify Your Email</h2>
                    
                    <p>Hi {full_name or 'there'},</p>
                    
                    <p>Thanks for signing up! Please verify your email address by clicking the link below:</p>
                    
                    <p style="margin: 30px 0;">
                        <a href="{verification_url}" style="display: inline-block; padding: 10px 20px; background-color: #3B82F6; color: white; text-decoration: none; border-radius: 5px;">
                            Verify Email
                        </a>
                    </p>
                    
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; color: #666;">{verification_url}</p>
                    
                    <p>This link will expire in 24 hours.</p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="color: #666; font-size: 12px;">
                        If you didn't create this account, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """

        plain_text = f"""
        Verify Your Email

        Hi {full_name or 'there'},

        Thanks for signing up! Please verify your email by clicking: {verification_url}

        This link will expire in 24 hours.

        If you didn't create this account, please ignore this email.
        """

        return self.send_email(to_email, subject, html_content, plain_text)

    def send_password_reset_email(
        self,
        to_email: str,
        full_name: Optional[str],
        token: str,
        frontend_url: str = "http://localhost:5173",
    ) -> bool:
        """Send password reset link."""
        reset_url = f"{frontend_url}/reset-password?token={token}"

        subject = "Reset Your Password"

        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Reset Your Password</h2>
                    
                    <p>Hi {full_name or 'there'},</p>
                    
                    <p>We received a request to reset your password. Click the link below to set a new password:</p>
                    
                    <p style="margin: 30px 0;">
                        <a href="{reset_url}" style="display: inline-block; padding: 10px 20px; background-color: #3B82F6; color: white; text-decoration: none; border-radius: 5px;">
                            Reset Password
                        </a>
                    </p>
                    
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="word-break: break-all; color: #666;">{reset_url}</p>
                    
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    
                    <p style="color: #666; font-size: 12px;">
                        If you didn't request a password reset, please ignore this email or contact support if you believe your account is at risk.
                    </p>
                </div>
            </body>
        </html>
        """

        plain_text = f"""
        Reset Your Password

        Hi {full_name or 'there'},

        We received a request to reset your password. Click the link to set a new password: {reset_url}

        This link will expire in 1 hour.

        If you didn't request this, please ignore this email.
        """

        return self.send_email(to_email, subject, html_content, plain_text)


def get_email_service() -> EmailService:
    """Get email service instance."""
    return EmailService()
