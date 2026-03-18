# AI Agent

A full-stack AI agent powered by **Anthropic Claude** with tool calling, persistent memory, CRM entities, scheduled automations, third-party integrations, and dual interfaces (Web UI + Telegram).

## Architecture

```
User → Telegram Bot ──┐
                       ├──► FastAPI Backend ──► Anthropic Claude API
User → React Web UI ──┘         │
                                ├── Tool Executor (web search, code exec, files, CRM, integrations)
                                ├── Memory Manager (conversation history + persistent notes)
                                ├── Entity/CRM Layer (Supabase)
                                ├── Scheduler (APScheduler CRON automations)
                                └── Integration Layer (OAuth → Gmail, Calendar)
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12, FastAPI, uvicorn |
| LLM | Anthropic Claude via `anthropic` SDK |
| Database | Supabase (PostgreSQL) |
| Scheduler | APScheduler |
| Telegram | python-telegram-bot v20+ |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Deployment | Docker + docker-compose |

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- A [Supabase](https://supabase.com) project (free tier works)
- An [Anthropic API key](https://console.anthropic.com)

### 1. Set Up Supabase

Create a new Supabase project, then run the schema SQL in the SQL Editor:

```
backend/supabase_schema.sql
```

This creates all required tables: `conversations`, `messages`, `memory_notes`, `entities`, `automations`, `integrations`.

### 2. Configure Environment

```bash
cp backend/.env.example backend/.env
```

Fill in your `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJ...  (service_role key)
```

### 3. Run the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### 5. Docker (optional)

```bash
docker-compose up --build
```

## API Endpoints

### Chat
- `POST /api/chat` — Send a message, get a response
- `GET /api/conversations` — List conversations
- `DELETE /api/conversations/{id}` — Delete conversation
- `WS /ws/chat` — WebSocket for streaming chat

### Entities (CRM)
- `GET /entities` — List entities
- `POST /entities` — Create entity
- `PATCH /entities/{id}` — Update entity
- `DELETE /entities/{id}` — Delete entity

### Automations
- `GET /automations` — List automations
- `POST /automations` — Create automation
- `PATCH /automations/{id}` — Update automation
- `DELETE /automations/{id}` — Delete automation

### Integrations
- `GET /integrations` — List connected integrations
- `GET /integrations/google/authorize` — Start Google OAuth flow
- `DELETE /integrations/{provider}` — Disconnect integration

### Admin
- `GET /api/admin/status` — System status
- `GET /api/admin/tools` — List registered tools
- `GET /api/admin/memory` — View memory notes
- `POST /api/admin/memory` — Create/update memory note
- `DELETE /api/admin/memory/{key}` — Delete memory note

### Telegram
- `POST /webhook/telegram` — Telegram webhook (set automatically)

## Tools

The agent has access to these tools:

| Tool | Description |
|------|-------------|
| `web_search` | Search the web via Tavily API |
| `execute_code` | Run Python code in a sandboxed environment |
| `read_file` / `write_file` / `list_files` | File operations in sandbox |
| `create_entity` / `search_entities` / `update_entity` / `delete_entity` | CRM operations |
| `save_memory` / `search_memory` | Long-term memory management |
| `send_email` / `list_inbox` | Gmail integration |
| `create_calendar_event` / `list_calendar_events` | Google Calendar integration |

## Configuration

### Optional Services

| Service | Env Var | Purpose |
|---------|---------|---------|
| Tavily | `TAVILY_API_KEY` | Web search |
| Telegram | `TELEGRAM_BOT_TOKEN` | Telegram bot |
| Google OAuth | `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` | Gmail & Calendar |
| Encryption | `ENCRYPTION_KEY` | Encrypt OAuth tokens at rest |

### Security

- Set `API_KEY` in `.env` to require Bearer token auth on all endpoints
- OAuth tokens are encrypted with Fernet before storage
- Code execution runs in a sandboxed subprocess with 30s timeout
- File operations are restricted to the sandbox directory

## Deployment

The application is production-ready and can be deployed to Railway in minutes.

### Quick Deploy (5 min)

1. **Configure environment** (`backend/.env`):
   ```bash
   SUPABASE_URL=<your-url>
   SUPABASE_KEY=<your-key>
   JWT_SECRET=<generate-random>
   SMTP_HOST=smtp.gmail.com
   SMTP_USER=<your-email>
   SMTP_PASSWORD=<app-password>
   ```

2. **Run migrations** in Supabase SQL Editor:
   - Execute all files: `backend/migrations/001-004`

3. **Deploy**:
   ```bash
   npm i -g @railway/cli
   railway init
   railway up
   ```

See [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) for detailed instructions.

### Features Included

✅ **User Authentication**
- JWT tokens with secure password hashing
- Email verification (auto-sent on signup)
- Password reset via email
- Protected routes

✅ **Email Service**
- Verification emails on signup
- Password reset emails
- Multiple SMTP providers (Gmail, SendGrid, Mailgun)
- Professional HTML templates

✅ **Security**
- Rate limiting (registration 5/min, login 10/min)
- CORS restricted to trusted origins
- Security headers (CSP, X-Frame-Options, etc.)
- Structured JSON logging

✅ **Development**
- Docker & docker-compose for local testing
- Test utilities included
- Comprehensive documentation

## Local Docker Development

```bash
# Build and start services
docker-compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:3000

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

See [`DOCKER_QUICK_START.md`](DOCKER_QUICK_START.md) for more details.

## Project Structure

```
ai-agent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings from env
│   │   ├── core/
│   │   │   ├── agent.py         # Core agent loop (the brain)
│   │   │   ├── llm.py           # Anthropic client
│   │   │   ├── system_prompt.py # Prompt assembly
│   │   │   └── conversation.py  # Conversation CRUD
│   │   ├── tools/               # All agent tools
│   │   ├── memory/              # Short-term + long-term memory
│   │   ├── entities/            # CRM CRUD + API
│   │   ├── automations/         # Scheduler + CRON jobs
│   │   ├── integrations/        # OAuth + Gmail + Calendar
│   │   ├── channels/            # Telegram + WebSocket
│   │   └── api/                 # REST endpoints + auth
│   ├── prompts/                 # System prompt templates
│   ├── supabase_schema.sql      # Database schema
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/               # Chat, Entities, Automations, etc.
│   │   ├── components/          # Sidebar, ChatMessage, ToolCallCard
│   │   ├── hooks/               # useWebSocket
│   │   └── lib/                 # API client
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```
