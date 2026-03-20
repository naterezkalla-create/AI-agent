"""Issue detection and automation suggestion services."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.automations.scheduler import add_automation_job, scheduler
from app.events.bus import event_bus
from app.memory.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _utcnow().isoformat()


def _base_issue_payload(
    *,
    user_id: str,
    kind: str,
    source_type: str,
    source_id: str,
    title: str,
    description: str,
    severity: str,
    confidence: float,
    suggested_action: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = _now_iso()
    return {
        "user_id": user_id,
        "kind": kind,
        "source_type": source_type,
        "source_id": source_id,
        "title": title,
        "description": description,
        "severity": severity,
        "confidence": confidence,
        "suggested_action": suggested_action,
        "status": "open",
        "metadata": metadata or {},
        "last_seen_at": now,
        "updated_at": now,
    }


async def list_issues(user_id: str, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    sb = get_supabase()
    query = sb.table("issues").select("*").eq("user_id", user_id)
    if status:
        query = query.eq("status", status)
    result = query.order("updated_at", desc=True).limit(limit).execute()
    return result.data


async def list_automation_suggestions(
    user_id: str,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    sb = get_supabase()
    query = sb.table("automation_suggestions").select("*").eq("user_id", user_id)
    if status:
        query = query.eq("status", status)
    result = query.order("updated_at", desc=True).limit(limit).execute()
    return result.data


async def upsert_issue(
    *,
    user_id: str,
    kind: str,
    source_type: str,
    source_id: str,
    title: str,
    description: str,
    severity: str,
    confidence: float,
    suggested_action: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sb = get_supabase()
    payload = _base_issue_payload(
        user_id=user_id,
        kind=kind,
        source_type=source_type,
        source_id=source_id,
        title=title,
        description=description,
        severity=severity,
        confidence=confidence,
        suggested_action=suggested_action,
        metadata=metadata,
    )

    existing = (
        sb.table("issues")
        .select("*")
        .eq("user_id", user_id)
        .eq("kind", kind)
        .eq("source_type", source_type)
        .eq("source_id", source_id)
        .neq("status", "resolved")
        .limit(1)
        .execute()
    )

    if existing.data:
        issue = (
            sb.table("issues")
            .update(payload)
            .eq("id", existing.data[0]["id"])
            .execute()
            .data[0]
        )
        action = "updated"
    else:
        issue = (
            sb.table("issues")
            .insert({**payload, "created_at": _now_iso()})
            .execute()
            .data[0]
        )
        action = "created"

    await event_bus.publish(
        "issues.changed",
        {"action": action, "issue": issue},
        user_id=user_id,
        topics={"issues"},
    )
    return issue


async def resolve_issue(issue_id: str, user_id: str, status: str = "resolved") -> dict[str, Any] | None:
    sb = get_supabase()
    updates = {
        "status": status,
        "updated_at": _now_iso(),
        "resolved_at": _now_iso() if status == "resolved" else None,
    }
    result = (
        sb.table("issues")
        .update(updates)
        .eq("id", issue_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        return None
    issue = result.data[0]
    await event_bus.publish(
        "issues.changed",
        {"action": "status_changed", "issue": issue},
        user_id=user_id,
        topics={"issues"},
    )
    return issue


async def _create_suggestion_for_issue(issue: dict[str, Any]) -> dict[str, Any] | None:
    sb = get_supabase()
    existing = (
        sb.table("automation_suggestions")
        .select("*")
        .eq("user_id", issue["user_id"])
        .eq("issue_id", issue["id"])
        .in_("status", ["proposed", "approved"])
        .limit(1)
        .execute()
    )
    if existing.data:
        return existing.data[0]

    suggestion: dict[str, Any] | None = None
    if issue["kind"] == "stale_entity":
        entity_name = issue.get("metadata", {}).get("entity_name", "contact")
        suggestion = {
            "user_id": issue["user_id"],
            "issue_id": issue["id"],
            "name": f"Follow up with {entity_name}",
            "prompt": f"Review the CRM entity '{entity_name}', summarize the missing next step, and draft a follow-up action or message.",
            "trigger_type": "event",
            "trigger_config": {"event_types": ["entities.changed"]},
            "cron_expression": "0 9 * * 1-5",
            "rationale": "This contact/deal has gone stale and likely needs a follow-up workflow.",
            "status": "proposed",
            "risk_level": "medium",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
    elif issue["kind"] == "automation_failure":
        auto_name = issue.get("metadata", {}).get("automation_name", "automation")
        suggestion = {
            "user_id": issue["user_id"],
            "issue_id": issue["id"],
            "name": f"Monitor {auto_name} failures",
            "prompt": f"Check why the automation '{auto_name}' failed recently, summarize root causes, and notify the user if it keeps failing.",
            "trigger_type": "event",
            "trigger_config": {"event_types": ["automations.changed"]},
            "cron_expression": "*/30 * * * *",
            "rationale": "Persistent automation failures should trigger a monitoring workflow.",
            "status": "proposed",
            "risk_level": "low",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
    elif issue["kind"] == "integration_attention":
        provider = issue.get("metadata", {}).get("provider", "integration")
        suggestion = {
            "user_id": issue["user_id"],
            "issue_id": issue["id"],
            "name": f"Reconnect {provider}",
            "prompt": f"Check the {provider} integration, summarize what broke, and remind the user to reconnect it if required.",
            "trigger_type": "event",
            "trigger_config": {"event_types": ["integrations.changed"]},
            "cron_expression": "0 */6 * * *",
            "rationale": "Integration outages should be actively monitored until resolved.",
            "status": "proposed",
            "risk_level": "low",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }

    if not suggestion:
        return None

    created = sb.table("automation_suggestions").insert(suggestion).execute().data[0]
    await event_bus.publish(
        "automation_suggestions.changed",
        {"action": "created", "suggestion": created},
        user_id=issue["user_id"],
        topics={"issues", "automation_suggestions"},
    )
    return created


async def approve_suggestion(suggestion_id: str, user_id: str) -> dict[str, Any] | None:
    sb = get_supabase()
    result = (
        sb.table("automation_suggestions")
        .select("*")
        .eq("id", suggestion_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        return None

    suggestion = result.data[0]
    if suggestion["status"] == "approved":
        return suggestion

    now = _now_iso()
    created = (
        sb.table("automations")
        .insert(
            {
                "user_id": user_id,
                "name": suggestion["name"],
                "cron_expression": suggestion.get("cron_expression") or "0 9 * * *",
                "prompt": suggestion["prompt"],
                "enabled": True,
                "trigger_type": suggestion.get("trigger_type") or "cron",
                "trigger_config": suggestion.get("trigger_config") or {},
                "max_retries": 2,
                "retry_delay_seconds": 60,
                "created_at": now,
            }
        )
        .execute()
        .data[0]
    )

    await add_automation_job(
        created["id"],
        user_id,
        created["name"],
        created["cron_expression"],
        created["prompt"],
        trigger_type=created.get("trigger_type", "cron"),
        trigger_config=created.get("trigger_config") or {},
        enabled=True,
        max_retries=created.get("max_retries", 2),
        retry_delay_seconds=created.get("retry_delay_seconds", 60),
    )

    updated = (
        sb.table("automation_suggestions")
        .update(
            {
                "status": "approved",
                "approved_at": now,
                "approved_automation_id": created["id"],
                "updated_at": now,
            }
        )
        .eq("id", suggestion_id)
        .execute()
        .data[0]
    )

    await event_bus.publish(
        "automation_suggestions.changed",
        {"action": "approved", "suggestion": updated, "automation": created},
        user_id=user_id,
        topics={"issues", "automation_suggestions", "automations"},
    )
    return updated


async def reject_suggestion(suggestion_id: str, user_id: str) -> dict[str, Any] | None:
    sb = get_supabase()
    result = (
        sb.table("automation_suggestions")
        .update({"status": "rejected", "updated_at": _now_iso()})
        .eq("id", suggestion_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        return None
    suggestion = result.data[0]
    await event_bus.publish(
        "automation_suggestions.changed",
        {"action": "rejected", "suggestion": suggestion},
        user_id=user_id,
        topics={"issues", "automation_suggestions"},
    )
    return suggestion


async def _detect_failed_automations(user_id: str) -> list[dict[str, Any]]:
    sb = get_supabase()
    result = (
        sb.table("automation_runs")
        .select("id, automation_id, status, error, created_at, automations(name)")
        .eq("user_id", user_id)
        .in_("status", ["failed", "retry_scheduled"])
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )

    issues = []
    for run in result.data:
        auto_name = ((run.get("automations") or {}) if isinstance(run.get("automations"), dict) else {}).get("name", "automation")
        issues.append(
            await upsert_issue(
                user_id=user_id,
                kind="automation_failure",
                source_type="automation",
                source_id=run["automation_id"],
                title=f"{auto_name} needs attention",
                description=run.get("error") or "An automation failed recently.",
                severity="high",
                confidence=0.95,
                suggested_action="Review the latest run and consider creating a monitoring automation.",
                metadata={"run_id": run["id"], "automation_name": auto_name, "status": run["status"]},
            )
        )
    return issues


async def _detect_integration_issues(user_id: str) -> list[dict[str, Any]]:
    sb = get_supabase()
    result = (
        sb.table("integrations")
        .select("*")
        .eq("user_id", user_id)
        .neq("status", "connected")
        .execute()
    )

    issues = []
    for integration in result.data:
        issues.append(
            await upsert_issue(
                user_id=user_id,
                kind="integration_attention",
                source_type="integration",
                source_id=integration["provider"],
                title=f"{integration['provider'].capitalize()} needs reconnecting",
                description=integration.get("last_error") or "The integration is not healthy.",
                severity="medium",
                confidence=0.9,
                suggested_action="Reconnect or reauthorize this integration.",
                metadata={"provider": integration["provider"], "status": integration.get("status")},
            )
        )
    return issues


async def _detect_stale_entities(user_id: str, days_without_update: int = 14) -> list[dict[str, Any]]:
    sb = get_supabase()
    cutoff = (_utcnow() - timedelta(days=days_without_update)).isoformat()
    result = (
        sb.table("entities")
        .select("*")
        .eq("user_id", user_id)
        .in_("type", ["contact", "lead", "deal"])
        .lt("updated_at", cutoff)
        .order("updated_at", desc=False)
        .limit(20)
        .execute()
    )

    issues = []
    for entity in result.data:
        entity_name = entity.get("data", {}).get("name") or entity.get("data", {}).get("company") or entity["type"]
        issues.append(
            await upsert_issue(
                user_id=user_id,
                kind="stale_entity",
                source_type="entity",
                source_id=entity["id"],
                title=f"{entity_name} is stale",
                description=f"This {entity['type']} has not been updated since {entity['updated_at'][:10]}.",
                severity="medium",
                confidence=0.75,
                suggested_action="Create a follow-up automation or review this record.",
                metadata={"entity_name": entity_name, "entity_type": entity["type"]},
            )
        )
    return issues


async def generate_suggestions_for_user(user_id: str) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    open_issues = await list_issues(user_id, status="open", limit=100)
    for issue in open_issues:
        suggestion = await _create_suggestion_for_issue(issue)
        if suggestion:
            suggestions.append(suggestion)
    return suggestions


async def scan_user_issues(user_id: str) -> dict[str, Any]:
    """Run built-in detectors for a user and generate suggestions."""
    issues: list[dict[str, Any]] = []
    issues.extend(await _detect_failed_automations(user_id))
    issues.extend(await _detect_integration_issues(user_id))
    issues.extend(await _detect_stale_entities(user_id))
    suggestions = await generate_suggestions_for_user(user_id)
    return {"issues": issues, "suggestions": suggestions}


def _collect_user_ids() -> set[str]:
    sb = get_supabase()
    user_ids: set[str] = set()
    tables_with_user_id = ["users", "automations", "integrations", "entities", "memory_notes", "conversations", "issues"]
    for table in tables_with_user_id:
        try:
            result = sb.table(table).select("user_id").execute()
            for row in result.data:
                value = row.get("user_id")
                if value:
                    user_ids.add(value)
        except Exception:
            continue
    if not user_ids:
        user_ids.add("default")
    return user_ids


async def scan_all_users() -> dict[str, Any]:
    summary: dict[str, Any] = {"users_scanned": 0, "issues": 0, "suggestions": 0}
    for user_id in _collect_user_ids():
        result = await scan_user_issues(user_id)
        summary["users_scanned"] += 1
        summary["issues"] += len(result["issues"])
        summary["suggestions"] += len(result["suggestions"])
    return summary


def start_issue_monitoring() -> None:
    """Schedule periodic issue scans on the shared scheduler."""
    if scheduler.get_job("issue-scan"):
        return
    scheduler.add_job(scan_all_users, "interval", minutes=15, id="issue-scan", replace_existing=True)
    logger.info("Issue monitoring scheduled")
