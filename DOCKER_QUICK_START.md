# Docker & Deployment Quick Start

## Local Docker Development (5 minutes)

### 1. Prepare Environment

```bash
cp backend/.env.example backend/.env

# Edit backend/.env with:
# SUPABASE_URL=<your-url>
# SUPABASE_KEY=<your-key>
# JWT_SECRET=<generate-random>
# SMTP settings (optional for testing)
```

### 2. Start Services

```bash
docker-compose up
```

### 3. Test

```bash
curl http://localhost:8000/health
open http://localhost:3000
```

---

## Deploy to Railway (10 minutes)

### 1. Create Railway Account

Go to [railway.app](https://railway.app) and sign up (free tier available).

### 2. Connect to GitHub

```bash
# Push your repo to GitHub
git push origin main
```

### 3. Create Railway Project

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Create and deploy
railway init
railway up
```

### 4. Set Environment Variables

In Railway dashboard → Variables:

```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...
JWT_SECRET=<generate-random-string>
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FRONTEND_URL=https://your-railway-domain.railway.app
```

### 5. Run Database Migrations

In Supabase SQL Editor, run all migrations:
- `backend/migrations/001_create_users_table.sql`
- `backend/migrations/002_add_api_keys.sql`
- `backend/migrations/003_create_user_settings.sql`
- `backend/migrations/004_add_email_verification.sql`

### 6. Deploy

```bash
railway up
```

Done! Your app is live 🎉

---

## Useful Docker Commands

```bash
# Build images
docker-compose build

# Start services (background)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Run single service
docker-compose up backend

# SSH into container
docker-compose exec backend bash

# See running containers
docker-compose ps
```

---

## Troubleshooting

### Port already in use
```bash
lsof -i :8000  # Find process
kill -9 <PID>  # Kill process
```

### Docker won't start
```bash
# Check Docker
docker ps

# Restart Docker daemon
# On macOS: Restart Docker Desktop
```

### Migration errors
```bash
# Check Supabase logs
# In Supabase → SQL Editor → check error messages
```

### Deployment failed
```bash
# Check Railway logs
railway logs

# Or in dashboard → Logs tab
```

See `DEPLOYMENT_GUIDE.md` for detailed troubleshooting.
