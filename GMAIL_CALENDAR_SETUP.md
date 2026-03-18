# Gmail & Google Calendar Integration Setup

## Status
- ✅ Encryption key: Generated and added to `.env`
- ✅ Backend tools: Ready (send_email, list_inbox, create_calendar_event, list_calendar_events)
- ✅ Frontend UI: Ready (Integrations page)
- ⏳ Google OAuth credentials: NEEDED

## Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **Create a new project:**
   - Click the project selector at the top
   - Select "NEW PROJECT"
   - Name: "AI Agent"
   - Click "CREATE"

3. **Enable APIs:**
   - Go to **APIs & Services → Library**
   - Search for "Gmail API" → Click → **ENABLE**
   - Search for "Google Calendar API" → Click → **ENABLE**

4. **Create OAuth Consent Screen:**
   - Go to **APIs & Services → OAuth consent screen**
   - Select **External** user type
   - Fill in:
     - App name: "AI Agent"
     - User support email: Your email
     - Developer contact: Your email
   - Click **SAVE AND CONTINUE** through all sections
   - Click **BACK TO DASHBOARD**

5. **Create OAuth Credentials:**
   - Go to **APIs & Services → Credentials**
   - Click **+ CREATE CREDENTIALS → OAuth client ID**
   - Application type: **Web application**
   - Name: "AI Agent Local"
   - Authorized JavaScript origins:
     - `http://localhost:8000`
     - `http://localhost:3000`
   - Authorized redirect URIs:
     - `http://localhost:8000/integrations/google/callback`
   - Click **CREATE**
   - Copy **Client ID** and **Client Secret**

## Step 2: Update `.env`

Edit `/Users/nate/Desktop/ai-agent/backend/.env`:

```
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE
GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
```

Restart the backend:
```bash
cd /Users/nate/Desktop/ai-agent/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

## Step 3: Test the Integration

1. Open http://localhost:3000 in your browser
2. Click **Integrations** in the sidebar
3. Click **Connect** on the Google card
4. Follow the Google OAuth prompts
5. You'll be redirected back to the integrations page
6. Try chatting: "List my emails" or "Create a calendar event for tomorrow at 2pm"

## Available Tools

Once connected, your agent can:

### Gmail
- `list_inbox` - List emails from inbox
- `send_email` - Send emails

### Google Calendar
- `list_calendar_events` - Show upcoming events
- `create_calendar_event` - Create new events

## Example Prompts

- "What emails did I receive today?"
- "Send an email to john@example.com with subject 'Meeting Update'"
- "Show my calendar for next week"
- "Create a meeting with the team tomorrow at 3pm for 1 hour"
