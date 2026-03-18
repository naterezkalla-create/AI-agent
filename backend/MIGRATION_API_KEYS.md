# Database Migration: Add API Keys Support

## Status
⚠️ **PENDING** - The `api_keys` column does not exist yet in the `user_settings` table.

## What This Adds
Adds a new `api_keys` JSONB column to store encrypted API keys per user.

## How to Run the Migration

### Option 1: Supabase SQL Editor (Recommended)

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to **SQL Editor** in the left sidebar
4. Click **New Query**
5. Copy and paste the SQL from [`002_add_api_keys.sql`](./002_add_api_keys.sql)
6. Click **Run**

### Option 2: Using psql (If you have PostgreSQL client installed)

```bash
# From backend directory
psql "postgresql://postgres:[PASSWORD]@[SUPABASE_HOST]:5432/postgres" << EOF
$(cat migrations/002_add_api_keys.sql)
EOF
```

Replace `[PASSWORD]` and `[SUPABASE_HOST]` with your Supabase credentials.

## The Migration SQL

```sql
ALTER TABLE user_settings 
ADD COLUMN IF NOT EXISTS api_keys JSONB DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_user_settings_api_keys ON user_settings USING GIN (api_keys);
```

## Verification

After running the migration, verify it worked:

```bash
cd /Users/nate/Desktop/ai-agent/backend
source venv/bin/activate
python3 check_schema.py
```

You should see:
```
✓ user_settings table exists
Columns: [..., 'api_keys', ...]
api_keys column exists: True
```

## What Changed

- **Column Name**: `api_keys`
- **Type**: `JSONB` (stores encrypted key data)
- **Default Value**: `{}` (empty object)
- **Index**: GIN index for fast queries
- **Purpose**: Stores encrypted API keys for services like Anthropic, OpenAI, GitHub

## Example Data Structure

Once added, the column will store data like:

```json
{
  "anthropic": "gAAAAABmDA5y...",
  "openai": "gAAAAABmDA5z...",
  "github_token": "gAAAAABmDA60..."
}
```

(Values are encrypted with Fernet cipher)
