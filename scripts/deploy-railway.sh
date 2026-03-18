#!/bin/bash
# Deploy to Railway using Railway CLI

set -e

echo "🚀 Deploying AI Agent to Railway..."
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed"
    echo "   Install from: https://docs.railway.app/guides/cli"
    exit 1
fi

# Link to Railway project
read -p "Enter your Railway project ID (from railway.app): " PROJECT_ID

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Project ID required"
    exit 1
fi

# Link project
echo ""
echo "🔗 Linking to Railway project..."
railway link "$PROJECT_ID" || true

# Deploy
echo ""
echo "📦 Deploying application..."
railway up

# Get deployment URL
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Go to https://railway.app/project to verify deployment"
echo "   2. Set environment variables in Railway dashboard:"
echo "      - SUPABASE_URL"
echo "      - SUPABASE_KEY"
echo "      - JWT_SECRET"
echo "      - SMTP settings"
echo "      - FRONTEND_URL (your Railway domain)"
echo "   3. Run database migrations in Supabase"
echo "   4. Visit your deployed application"
