from app.tools.base import BaseTool
from app.integrations.gmail import send_email, list_inbox
from app.integrations.google_calendar import create_event, list_events
from app.integrations.external_services import (
    apify_run_actor,
    github_list_issues,
    github_list_repos,
    notion_create_page,
    notion_search,
    slack_post_message,
)


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


class SlackPostMessageTool(BaseTool):
    @property
    def name(self) -> str:
        return "slack_post_message"

    @property
    def description(self) -> str:
        return "Send a Slack message to a channel or user. Requires Slack integration."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Slack channel ID, user ID, or channel name"},
                "text": {"type": "string", "description": "Message body"},
            },
            "required": ["channel", "text"],
        }

    async def execute(self, channel: str, text: str, user_id: str = "default") -> str:
        return await slack_post_message(user_id, channel, text)


class GitHubListReposTool(BaseTool):
    @property
    def name(self) -> str:
        return "github_list_repos"

    @property
    def description(self) -> str:
        return "List the connected user's GitHub repositories."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum repositories to return (default: 10)",
                    "default": 10,
                }
            },
        }

    async def execute(self, limit: int = 10, user_id: str = "default") -> list:
        return await github_list_repos(user_id, limit)


class GitHubListIssuesTool(BaseTool):
    @property
    def name(self) -> str:
        return "github_list_issues"

    @property
    def description(self) -> str:
        return "List issues from a GitHub repository."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner or organization"},
                "repo": {"type": "string", "description": "Repository name"},
                "state": {"type": "string", "description": "Issue state: open, closed, or all", "default": "open"},
                "limit": {"type": "integer", "description": "Maximum issues to return (default: 10)", "default": 10},
            },
            "required": ["owner", "repo"],
        }

    async def execute(self, owner: str, repo: str, state: str = "open", limit: int = 10, user_id: str = "default") -> list:
        return await github_list_issues(user_id, owner, repo, state, limit)


class NotionSearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "notion_search"

    @property
    def description(self) -> str:
        return "Search the connected Notion workspace for pages and databases."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search phrase"},
                "limit": {"type": "integer", "description": "Maximum results to return (default: 10)", "default": 10},
            },
            "required": ["query"],
        }

    async def execute(self, query: str, limit: int = 10, user_id: str = "default") -> list:
        return await notion_search(user_id, query, limit)


class NotionCreatePageTool(BaseTool):
    @property
    def name(self) -> str:
        return "notion_create_page"

    @property
    def description(self) -> str:
        return "Create a page inside an existing Notion page."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "parent_page_id": {"type": "string", "description": "Parent Notion page ID"},
                "title": {"type": "string", "description": "Page title"},
                "content": {"type": "string", "description": "Initial page content"},
            },
            "required": ["parent_page_id", "title"],
        }

    async def execute(self, parent_page_id: str, title: str, content: str = "", user_id: str = "default") -> dict:
        return await notion_create_page(user_id, parent_page_id, title, content)


class ApifyRunActorTool(BaseTool):
    @property
    def name(self) -> str:
        return "apify_run_actor"

    @property
    def description(self) -> str:
        return "Run an Apify actor with optional JSON input."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "actor_id": {"type": "string", "description": "Apify actor ID, username/actor-name, or actor task target"},
                "actor_input": {"type": "object", "description": "JSON input payload for the actor"},
            },
            "required": ["actor_id"],
        }

    async def execute(self, actor_id: str, actor_input: dict | None = None, user_id: str = "default") -> dict:
        return await apify_run_actor(user_id, actor_id, actor_input)
