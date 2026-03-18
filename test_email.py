#!/usr/bin/env python3
"""
Email service test script.
Run this to verify email configuration and test email sending.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.config import get_settings
from app.services.email import get_email_service


def test_email_configuration():
    """Test email service configuration."""
    print("📧 Email Service Configuration Test\n")
    
    settings = get_settings()
    
    print("Configuration:")
    print(f"  SMTP Host: {settings.smtp_host or '❌ NOT SET'}")
    print(f"  SMTP Port: {settings.smtp_port}")
    print(f"  SMTP User: {settings.smtp_user or '❌ NOT SET'}")
    print(f"  From Email: {settings.from_email or '❌ NOT SET'}")
    print(f"  From Name: {settings.from_name}")
    print(f"  Frontend URL: {settings.frontend_url}")
    
    # Check if email service is configured
    if not settings.smtp_host or not settings.smtp_user:
        print("\n⚠️  Email service is not fully configured.")
        print("   Add SMTP_HOST, SMTP_USER, SMTP_PASSWORD, and FROM_EMAIL to .env")
        return False
    
    print("\n✅ Email configuration looks good!")
    return True


def test_email_send(email: str):
    """Test sending an email."""
    print(f"\n📧 Sending test email to {email}...\n")
    
    email_service = get_email_service()
    
    # Test verification email
    print("Testing verification email...")
    result = email_service.send_verification_email(
        to_email=email,
        full_name="Test User",
        token="test-verification-token-abc123",
        frontend_url="http://localhost:5173"
    )
    
    if result:
        print("  ✅ Verification email sent successfully")
    else:
        print("  ❌ Failed to send verification email")
        return False
    
    # Test password reset email
    print("\nTesting password reset email...")
    result = email_service.send_password_reset_email(
        to_email=email,
        full_name="Test User",
        token="test-reset-token-xyz789",
        frontend_url="http://localhost:5173"
    )
    
    if result:
        print("  ✅ Password reset email sent successfully")
    else:
        print("  ❌ Failed to send password reset email")
        return False
    
    return True


def main():
    """Run email service tests."""
    print("\n" + "="*50)
    print("Email Service Test Suite")
    print("="*50 + "\n")
    
    # Test configuration
    configured = test_email_configuration()
    
    if not configured:
        print("\n💡 To configure email service:")
        print("   1. Update backend/.env with SMTP settings")
        print("   2. See EMAIL_SETUP.md for detailed instructions")
        print("   3. Gmail users: Use app password from https://myaccount.google.com/apppasswords")
        return
    
    # Ask if user wants to test sending
    print("\n" + "-"*50)
    email = input("\n📧 Enter email address to test with (or press Enter to skip): ").strip()
    
    if email:
        if test_email_send(email):
            print("\n✅ All email tests passed!")
        else:
            print("\n❌ Email tests failed. Check your configuration.")
    else:
        print("\nℹ️  Email configuration test passed, but skipped sending test email.")
    
    print("\n" + "="*50 + "\n")


if __name__ == "__main__":
    main()
