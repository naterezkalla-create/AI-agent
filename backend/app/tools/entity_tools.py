import json
from datetime import datetime, timezone
from app.tools.base import BaseTool
from app.memory.supabase_client import get_supabase


class CreateEntityTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_entity"

    @property
    def description(self) -> str:
        return "Create a new CRM entity (contact, deal, note, call_log, or custom type). Store structured data about people, deals, or anything the user wants to track."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "entity_type": {
                    "type": "string",
                    "description": "Type of entity: contact, deal, note, call_log, or any custom type",
                },
                "data": {
                    "type": "object",
                    "description": "The entity data as key-value pairs. E.g. {\"name\": \"John\", \"email\": \"john@example.com\", \"company\": \"Acme\"}",
                },
            },
            "required": ["entity_type", "data"],
        }

    async def execute(self, entity_type: str, data: dict, user_id: str = "default") -> str:
        sb = get_supabase()
        now = datetime.now(timezone.utc).isoformat()
        result = sb.table("entities").insert({
            "user_id": user_id,
            "type": entity_type,
            "data": data,
            "created_at": now,
            "updated_at": now,
        }).execute()

        entity = result.data[0]
        return f"Created {entity_type} entity (ID: {entity['id']}): {json.dumps(data, default=str)}"


class SearchEntitiesTool(BaseTool):
    @property
    def name(self) -> str:
        return "search_entities"

    @property
    def description(self) -> str:
        return "Search CRM entities by type and/or keyword. Returns matching entities."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "entity_type": {
                    "type": "string",
                    "description": "Filter by entity type (optional)",
                },
                "query": {
                    "type": "string",
                    "description": "Search keyword to match against entity data (optional)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default: 20)",
                    "default": 20,
                },
            },
        }

    async def execute(self, entity_type: str = None, query: str = None, limit: int = 20, user_id: str = "default") -> list:
        sb = get_supabase()
        q = sb.table("entities").select("*").eq("user_id", user_id)

        if entity_type:
            q = q.eq("type", entity_type)

        result = q.order("created_at", desc=True).limit(limit).execute()

        entities = result.data
        # Client-side keyword filter on JSON data if query provided
        if query and entities:
            query_lower = query.lower()
            entities = [
                e for e in entities
                if query_lower in json.dumps(e.get("data", {}), default=str).lower()
            ]

        return [
            {"id": e["id"], "type": e["type"], "data": e["data"], "created_at": e["created_at"]}
            for e in entities
        ]


class UpdateEntityTool(BaseTool):
    @property
    def name(self) -> str:
        return "update_entity"

    @property
    def description(self) -> str:
        return "Update an existing CRM entity by its ID. Merges new data with existing data."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The UUID of the entity to update",
                },
                "data": {
                    "type": "object",
                    "description": "New data to merge with existing entity data",
                },
            },
            "required": ["entity_id", "data"],
        }

    async def execute(self, entity_id: str, data: dict, user_id: str = "default") -> str:
        sb = get_supabase()

        # Fetch existing
        existing = sb.table("entities").select("*").eq("id", entity_id).eq("user_id", user_id).execute()
        if not existing.data:
            return f"Entity not found: {entity_id}"

        # Merge data
        merged = {**existing.data[0].get("data", {}), **data}
        now = datetime.now(timezone.utc).isoformat()
        sb.table("entities").update({
            "data": merged,
            "updated_at": now,
        }).eq("id", entity_id).eq("user_id", user_id).execute()

        return f"Updated entity {entity_id}: {json.dumps(merged, default=str)}"


class DeleteEntityTool(BaseTool):
    @property
    def name(self) -> str:
        return "delete_entity"

    @property
    def description(self) -> str:
        return "Delete a CRM entity by its ID."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "The UUID of the entity to delete",
                },
            },
            "required": ["entity_id"],
        }

    async def execute(self, entity_id: str, user_id: str = "default") -> str:
        sb = get_supabase()
        result = sb.table("entities").delete().eq("id", entity_id).eq("user_id", user_id).execute()
        if result.data:
            return f"Deleted entity {entity_id}"
        return f"Entity not found: {entity_id}"
