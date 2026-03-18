#!/bin/bash
# Run database migrations

set -e

echo "🗄️  AI Agent Database Migrations"
echo ""

# Check which migration files exist
echo "📋 Available migrations:"
ls -1 backend/migrations/*.sql | nl

echo ""
echo "⚠️  Before running migrations:"
echo "   1. Backup your Supabase database"
echo "   2. Ensure SUPABASE_URL and SUPABASE_KEY are set in .env"
echo "   3. Review migration files in backend/migrations/"
echo ""

read -p "Have you backed up your database? (yes/no): " backup_confirmed

if [ "$backup_confirmed" != "yes" ]; then
    echo "❌ Backup not confirmed. Exiting."
    exit 1
fi

echo ""
echo "To run migrations, follow these steps:"
echo ""
echo "1. Go to Supabase dashboard → SQL Editor"
echo "2. Click 'New Query' for each migration file:"
echo ""

for migration in backend/migrations/*.sql; do
    filename=$(basename "$migration")
    echo "   📄 $filename"
done

echo ""
echo "3. Copy and paste each migration SQL into Supabase"
echo "4. Run each migration in order (001, 002, 003, 004)"
echo "5. Verify tables and columns were created"
echo ""
echo "📚 For automated migration support in future:"
echo "   - Consider using Supabase migration tools"
echo "   - Or use Alembic for Python migrations"
