# Production Deployment Checklist

Complete this checklist before deploying to production.

## 🔧 Pre-Deployment Configuration

### Environment Variables
- [ ] Generate JWT_SECRET: `openssl rand -hex 32`
- [ ] Get SUPABASE_URL from Supabase dashboard
- [ ] Get SUPABASE_KEY (service_role key)
- [ ] Configure SMTP service (Gmail/SendGrid/Mailgun)
- [ ] Set FROM_EMAIL and FROM_NAME
- [ ] Set FRONTEND_URL to your production domain
- [ ] All variables added to `.env` and Railway dashboard

### Database
- [ ] Supabase project created
- [ ] All 4 migration files executed in order:
  - [ ] `001_create_users_table.sql`
  - [ ] `002_add_api_keys.sql`
  - [ ] `003_create_user_settings.sql`
  - [ ] `004_add_email_verification.sql`
- [ ] Migrations verified (tables/columns exist)
- [ ] Database backup configured in Supabase
- [ ] Connection from backend tested

### Security
- [ ] JWT_SECRET is strong random value (32+ chars)
- [ ] JWT_SECRET is kept secret (not in git)
- [ ] SMTP_PASSWORD is kept secret (not in git)
- [ ] .env file is in .gitignore
- [ ] No credentials in git history
- [ ] CORS configured for production domain
- [ ] HTTPS/SSL enabled (Railway automatic)
- [ ] Security headers enabled (✅ already in code)
- [ ] Rate limiting enabled (✅ already in code)

### Email Service
- [ ] SMTP credentials obtained (Gmail/SendGrid/etc)
- [ ] Email service tested: `python3 test_email.py`
- [ ] Test email received successfully
- [ ] Verification and reset emails tested
- [ ] FROM_EMAIL whitelisted with email service

### Frontend
- [ ] Build succeeds: `npm run build`
- [ ] No TypeScript errors
- [ ] Environment correct for production
- [ ] API URL points to backend domain

### Backend  
- [ ] All Python files compile
- [ ] No import errors
- [ ] Requirements.txt up to date
- [ ] Health check working: `GET /health`
- [ ] API endpoints tested locally

## 🐳 Docker & Deployment

### Docker Setup
- [ ] Backend Dockerfile exists and builds
- [ ] Frontend Dockerfile exists and builds
- [ ] docker-compose.yml configured
- [ ] .dockerignore files created
- [ ] Local Docker test successful
- [ ] Port 8000 and 3000 accessible

### Railway Setup
- [ ] Railway account created
- [ ] Railway CLI installed: `railway --version`
- [ ] railway.toml configured
- [ ] GitHub repository created
- [ ] Code pushed to GitHub
- [ ] Railway project linked: `railway link <id>`

### Deployment
- [ ] Dockerfile path correct in railway.toml
- [ ] Start command correct
- [ ] Health check path correct
- [ ] All environment variables added to Railway
- [ ] Deployment succeeds: `railway up`
- [ ] Backend health check passes
- [ ] Frontend loads without errors

## ✅ Post-Deployment Testing

### Authentication
- [ ] Can sign up with valid email/password
- [ ] Verification email received
- [ ] Can click verification link and verify email
- [ ] Can login after verification
- [ ] Can logout
- [ ] Protected routes redirect to login when not authenticated

### Password Reset
- [ ] Can click "Forgot password?" on login
- [ ] Can submit email address
- [ ] Reset email received
- [ ] Can click reset link
- [ ] Can set new password
- [ ] Can login with new password

### API
- [ ] GET /health returns 200
- [ ] GET / returns app info
- [ ] Rate limiting works (test with multiple requests)
- [ ] CORS headers present
- [ ] Security headers present

### Database
- [ ] User data saved to Supabase
- [ ] User settings created automatically
- [ ] Verification tokens stored
- [ ] Password hashes not stored plaintext

### Monitoring
- [ ] Can view logs in Railway dashboard
- [ ] No errors in logs
- [ ] Response times acceptable
- [ ] CPU/Memory usage reasonable

## 📊 Performance & Load

- [ ] Application loads quickly
- [ ] No N+1 database queries
- [ ] Images and assets compressed
- [ ] CDN working (if configured)

## 🔐 Security Verification

- [ ] HTTPS enabled (green lock icon)
- [ ] No mixed content warnings
- [ ] CSP headers allow only trusted sources
- [ ] X-Frame-Options prevents clickjacking
- [ ] CORS prevents unauthorized origins
- [ ] Rate limiting preventing abuse
- [ ] Passwords not visible in logs
- [ ] API keys encrypted

## 📋 Documentation

- [ ] README.md updated with deployment info
- [ ] DEPLOYMENT_GUIDE.md created
- [ ] DOCKER_QUICK_START.md created
- [ ] EMAIL_SETUP.md created
- [ ] Architecture documented
- [ ] Runbook for common issues

## 🚀 Go Live

Only when all boxes are checked:

- [ ] Run final health check
- [ ] Notify team of deployment
- [ ] Monitor for errors
- [ ] Have rollback plan ready
- [ ] Document deployment date/time
- [ ] Update status page if applicable

## 📞 Post-Launch

- [ ] Monitor logs for errors
- [ ] Monitor database performance
- [ ] Monitor CPU/memory usage
- [ ] Set up error tracking (Sentry, etc)
- [ ] Set up uptime monitoring
- [ ] Have incident response plan

## 📝 Maintenance Schedule

- [ ] Daily: Check logs for errors
- [ ] Weekly: Monitor metrics and performance
- [ ] Monthly: Update dependencies
- [ ] Quarterly: Security review
- [ ] Annually: Disaster recovery drill

---

## Quick Commands Reference

```bash
# Local testing
docker-compose up
npm run build
python3 test_email.py

# Deployment
railway init
railway up
railway logs

# Database
# In Supabase SQL Editor:
# Copy and run migration files

# Emergency
railway down  # Stop deployment
git revert    # Rollback code
```

---

## Support

- Railway Docs: https://docs.railway.app
- Supabase Docs: https://supabase.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com
- Project Issues: Check GitHub Issues

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Notes**: _______________
