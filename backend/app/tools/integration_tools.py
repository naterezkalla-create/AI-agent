from app.tools.base import BaseTool
from app.integrations.gmail import send_email, list_inbox
from app.integrations.google_calendar import create_event, list_events


class SendEmailTool(BaseTool):
    @property
    def name(self) -> str:
        return "send_email"

    @property
    def description(self) -> str:
        return "Send an email via Gmail on behalf of the user. Requires Gmail integration to be connected."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject line"},
                "body": {"type": "string", "description": "Email body (plain text)"},
            },
            "required": ["to", "subject", "body"],
        }

    async def execute(self, to: str, subject: str, body: str, user_id: str = "default") -> str:
        return await send_email(user_id, to, subject, body)


class ListInboxTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_inbox"

    @property
    def description(self) -> str:
        return "List recent emails from the user's Gmail inbox. Requires Gmail integration to be connected."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum emails to retrieve (default: 10)",
                    "default": 10,
                },
                "query": {
                    "type": "string",
                    "description": "Gmail search query (optional, e.g. 'from:boss@company.com')",
                },
            },
        }

    async def execute(self, max_results: int = 10, query: str = "", user_id: str = "default") -> str:
        return await list_inbox(user_id, max_results, query)


class CreateCalendarEventTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_calendar_event"

    @property
    def description(self) -> str:
        return "Create a new event on the user's Google Calendar. Requires Calendar integration to be connected."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Event title"},
                "start_time": {"type": "string", "description": "Start time in ISO 8601 format (e.g., '2025-03-20T14:00:00-05:00')"},
                "end_time": {"type": "string", "description": "End time in ISO 8601 format"},
                "description": {"type": "string", "description": "Event description (optional)"},
                "location": {"type": "string", "description": "Event location (optional)"},
            },
            "required": ["title", "start_time", "end_time"],
        }

    async def execute(self, title: str, start_time: str, end_time: str, description: str = "", location: str = "", user_id: str = "default") -> str:
        return await create_event(user_id, title, start_time, end_time, description, location)


class ListCalendarEventsTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_calendar_events"

    @property
    def description(self) -> str:
        return "List upcoming events from the user's Google Calendar. Requires Calendar integration to be connected."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum events to retrieve (default: 10)",
                    "default": 10,
                },
                "time_min": {
                    "type": "string",
                    "description": "Start of time range in ISO 8601 (defaults to now)",
                },
            },
        }

    async def execute(self, max_results: int = 10, time_min: str = "", user_id: str = "default") -> str:
        return await list_events(user_id, max_results, time_min)
