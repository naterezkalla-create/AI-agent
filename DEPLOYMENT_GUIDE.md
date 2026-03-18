# Deployment Guide

This guide walks you through deploying the AI Agent application to production on Railway.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [Local Docker Testing](#local-docker-testing)
4. [Railway Deployment](#railway-deployment)
5. [Post-Deployment](#post-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

- ✅ [Docker](https://docker.com) installed and running
- ✅ [Railway CLI](https://docs.railway.app/guides/cli) installed
- ✅ [Railway](https://railway.app) account (free tier available)
- ✅ [Supabase](https://supabase.com) PostgreSQL database set up
- ✅ Email service credentials (Gmail SMTP or SendGrid)
- ✅ Secure JWT_SECRET generated
- ✅ All environment variables prepared

---

## Database Setup

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Copy project `URL` and `API Key` (service_role key)
4. Add to `.env`:
   ```bash
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=eyJhbGc...
   ```

### 2. Run Migrations

1. In Supabase dashboard, go to **SQL Editor**
2. Create a new query for each migration file:
   - `backend/migrations/001_create_users_table.sql`
   - `backend/migrations/002_add_api_keys.sql`
   - `backend/migrations/003_create_user_settings.sql`
   - `backend/migrations/004_add_email_verification.sql`

3. Copy SQL from each file and run in Supabase

**Note**: Run migrations in order (001, 002, 003, 004)

### 3. Verify Migrations

In Supabase SQL Editor, run:

```sql
-- Check users table
SELECT * FROM information_schema.tables WHERE table_name = 'users';

-- Check user_settings table
SELECT * FROM information_schema.tables WHERE table_name = 'user_settings';

-- Check columns
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;
```

---

## Local Docker Testing

### 1. Prepare Environment

```bash
cd /Users/nate/Desktop/ai-agent

# Copy environment template
cp backend/.env.example backend/.env

# Edit .env with your values:
# - SUPABASE_URL and SUPABASE_KEY
# - JWT_SECRET (generate: openssl rand -hex 32)
# - SMTP settings
# - FRONTEND_URL (use http://localhost:3000 for testing)
```

### 2. Build and Run Locally

```bash
# Option A: Using Docker Compose (Recommended)
docker-compose up

# Option B: Using script
chmod +x scripts/dev-docker.sh
./scripts/dev-docker.sh
```

### 3. Test Locally

```bash
# Backend health check
curl http://localhost:8000/health

# Frontend
open http://localhost:3000

# Test signup
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'
```

### 4. Stop Services

```bash
docker-compose down
```

---

## Railway Deployment

### 1. Initialize Railway Project

```bash
# Login to Railway
railway login

# Create new project
railway init

# Or link to existing project
railway link <project-id>
```

### 2. Deploy with Railway CLI

```bash
chmod +x scripts/deploy-railway.sh
./scripts/deploy-railway.sh
```

Or manually:

```bash
railway up
```

### 3. Configure Environment Variables

In Railway dashboard:

1. Go to your project
2. Click **Variables**
3. Add all required variables:

   ```
   SUPABASE_URL=<your-supabase-url>
   SUPABASE_KEY=<your-supabase-key>
   JWT_SECRET=<secure-random-string>
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_HOURS=168
   
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=<your-email>
   SMTP_PASSWORD=<app-password>
   FROM_EMAIL=<sender-email>
   FROM_NAME=AI Agent
   
   FRONTEND_URL=https://<your-railway-domain>
   DEBUG=false
   ```

### 4. Deploy

```bash
railway up
```

### 5. Get Your URL

After deployment, Railway will provide:
- Backend URL: `https://ai-agent-backend.railway.app`
- Frontend URL: `https://ai-agent-frontend.railway.app`

Update `FRONTEND_URL` environment variable with your actual domain if using custom domain.

---

## Post-Deployment

### 1. Verify Deployment

```bash
# Check backend health
curl https://your-railway-backend-url/health

# Should return: {"status": "ok"}
```

### 2. Test Authentication Flow

1. Visit frontend URL
2. Sign up with test account
3. Check email for verification link
4. Click verification link
5. Login with credentials

### 3. Test Password Reset

1. Login to app
2. Click "Forgot password?" on login page
3. Enter email address
4. Check email for reset link
5. Click reset link and set new password

### 4. Monitor Logs

```bash
# View Railway logs
railway logs

# Or in dashboard: Logs tab
```

### 5. Set Up Custom Domain (Optional)

In Railway dashboard:

1. Click **Settings** → **Domain**
2. Add custom domain
3. Update DNS records
4. Update `FRONTEND_URL` environment variable

---

## Production Checklist

Before going live:

- [ ] Database migrations executed
- [ ] All environment variables set
- [ ] Email service configured and tested
- [ ] JWT_SECRET is strong random value
- [ ] Backend health check passes
- [ ] Frontend loads without errors
- [ ] Can sign up, receive email, verify
- [ ] Can reset password via email
- [ ] CORS configured correctly
- [ ] SSL/TLS certificate valid
- [ ] Monitoring and error tracking enabled
- [ ] Database backup configured

---

## Troubleshooting

### Backend won't start

```bash
# Check logs
railway logs

# Common issues:
# - Missing environment variables → Add to Railway dashboard
# - Database connection → Verify SUPABASE_URL and SUPABASE_KEY
# - Port binding → Railway automatically handles
```

### Emails not sending

```bash
# Test email configuration
python3 test_email.py

# Common issues:
# - Gmail: Enable 2FA, create app password
# - SendGrid: Verify API key
# - SMTP_* variables: Check spelling and values
```

### Database migration errors

```sql
-- Check migration status
SELECT * FROM information_schema.tables 
WHERE table_name = 'users';

-- If table missing, check error in Supabase SQL Editor
-- Re-run migration if needed
```

### Frontend won't connect to backend

```
Check:
- CORS settings in backend (should allow your frontend domain)
- Frontend VITE_API_URL configuration
- Backend domain in HTTP browser console
- Network tab in browser DevTools
```

### Authentication fails after deployment

```
Check:
- JWT_SECRET is set and same across deployments
- Tokens are being stored in localStorage
- API returns correct response format
- Check browser console for errors
```

---

## Scaling and Maintenance

### Monitor Performance

- Check Railway dashboard metrics (CPU, memory, requests)
- Monitor database query performance
- Set up error tracking (Sentry, LogRocket, etc.)

### Update Environment

```bash
# Update backend code
git push heroku main  # Or Railway equivalent

# Run migrations for schema changes
# Done in Supabase SQL Editor

# Update environment variables
# Done in Railway dashboard
```

### Backup Database

```bash
# Supabase automatically backs up
# Manual backup:
# Go to Supabase dashboard → Backups

# Download backup if needed
```

### SSL Certificate

Railway provides free Let's Encrypt certificates. No action needed.

---

## Getting Help

- [Railway Docs](https://docs.railway.app)
- [Supabase Docs](https://supabase.com/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Railway Community](https://discord.gg/railway)

---

## Next Steps

After successful deployment:

1. ✅ Monitor application for errors
2. ✅ Test all user flows with real users
3. ✅ Collect feedback
4. ✅ Plan feature improvements
5. ✅ Scale if needed (increase Railway resources)

Congratulations! Your AI Agent is live! 🎉
