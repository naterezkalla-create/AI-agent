# Email Service Setup Guide

The application now includes a complete email service for sending verification emails and password reset links.

## Configuration

Add these variables to your `.env` file:

```bash
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=AI Agent
FRONTEND_URL=http://localhost:5173
```

## Gmail Setup (Recommended for Development)

1. **Enable 2-Factor Authentication** on your Google Account
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Create an App Password**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer" (or your device)
   - Google will generate a 16-character password
   - Copy this as your `SMTP_PASSWORD`

3. **Add to .env**
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # (paste the 16-char password)
   FROM_EMAIL=your-email@gmail.com
   FROM_NAME=AI Agent
   ```

## Alternative Email Services

### SendGrid
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.xxxxx...  # Your SendGrid API key
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=AI Agent
```

### Mailgun
```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@yourdomain.mailgun.org
SMTP_PASSWORD=your-mailgun-password
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=AI Agent
```

### AWS SES
```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=AI Agent
```

## Testing Email Service

With the configuration in place, the following flows will automatically send emails:

### 1. Email Verification
- User signs up → Verification email sent
- User clicks verification link → Email marked as verified
- Can resend verification email via `/api/auth/resend-verification-email`

### 2. Password Reset
- User clicks "Forgot password?" → Password reset email sent
- User clicks reset link → Can set new password
- Token expires in 1 hour

## Email Suppression (Development)

If you want to disable email sending in development without removing the SMTP config, emails will automatically be skipped if `SMTP_HOST` is empty.

The service logs all email operations:

```python
# Check logs for email debugging
# Successful: "Email sent successfully to user@example.com"
# Failed: "Failed to send email to user@example.com: [error details]"
```

## Testing Without Email Service

For testing without configuring SMTP, the API endpoints will still work:

- Email verification tokens are still generated and stored
- Email endpoints return success messages
- Tokens can be verified via direct database queries
- The `verify-email` and `reset-password` endpoints will work if you provide valid tokens

## Security Notes

🔒 **Never commit your SMTP credentials to version control**
- Add `.env` to `.gitignore` (already done)
- Use `.env.example` as template with placeholder values

🔒 **For Production**
- Use a dedicated email service (SendGrid, Mailgun, etc.)
- Store SMTP password in environment variables/secrets manager
- Consider using OAuth2 instead of app passwords
- Enable TLS/SSL for SMTP connections
- Monitor email delivery and bounces

## Troubleshooting

### "connection refused" errors
- Verify SMTP_HOST and SMTP_PORT are correct
- Check if firewall is blocking port 587
- For Gmail: Verify app password is correct (not regular password)

### "invalid credentials" errors
- Verify SMTP_USER and SMTP_PASSWORD match your email service
- For Gmail: Ensure 2FA is enabled and using app password
- Check that special characters in password are escaped

### Emails not received
- Check inbox and spam folders
- Verify FROM_EMAIL is correct and whitelisted
- Check email service logs/dashboard
- Ensure FRONTEND_URL is correct for links

### Logs show "Email service not configured"
- This is normal if SMTP_HOST is empty in .env
- Email endpoints will still function normally
- No emails will be sent until SMTP is configured
