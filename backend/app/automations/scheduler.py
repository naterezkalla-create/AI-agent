"""APScheduler setup plus durable automation runtime tracking."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.events.bus import event_bus
from app.memory.supabase_client import get_supabase

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
event_automations: dict[str, dict[str, Any]] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utcnow().isoformat()


def _normalize_automation(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized.setdefault("trigger_type", "cron")
    normalized.setdefault("trigger_config", {})
    normalized.setdefault("max_retries", 2)
    normalized.setdefault("retry_delay_seconds", 60)
    return normalized


def _parse_cron(expression: str) -> dict:
    """Parse a cron expression into APScheduler CronTrigger kwargs."""
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression (need 5 parts): {expression}")

    fields = ["minute", "hour", "day", "month", "day_of_week"]
    result = {}
    for field, value in zip(fields, parts):
        if value != "*":
            result[field] = value
    return result


def _event_matches(automation: dict[str, Any], event_type: str) -> bool:
    trigger_config = automation.get("trigger_config") or {}
    event_types = trigger_config.get("event_types") or []
    return not event_types or event_type in event_types


def _upsert_automation_run(
    *,
    run_id: str | None = None,
    automation_id: str,
    user_id: str,
    trigger_type: str,
    trigger_payload: dict[str, Any],
    status: str,
    attempt: int,
    error: str | None = None,
    result_summary: str | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
    next_retry_at: str | None = None,
) -> dict[str, Any]:
    sb = get_supabase()
    payload = {
        "automation_id": automation_id,
        "user_id": user_id,
        "trigger_type": trigger_type,
        "trigger_payload": trigger_payload,
        "status": status,
        "attempt": attempt,
        "error": error,
        "result_summary": result_summary,
        "started_at": started_at,
        "finished_at": finished_at,
        "next_retry_at": next_retry_at,
    }
    if run_id:
        result = sb.table("automation_runs").update(payload).eq("id", run_id).execute()
    else:
        payload["created_at"] = _iso_now()
        result = sb.table("automation_runs").insert(payload).execute()
    return result.data[0]


async def _publish_run_event(event_type: str, run: dict[str, Any], automation: dict[str, Any]) -> None:
    await event_bus.publish(
        event_type,
        {
            "automation_id": automation["id"],
            "automation_name": automation.get("name"),
            "run": run,
        },
        user_id=automation.get("user_id", "default"),
        topics={"automations", "automation_runs"},
    )


async def _execute_automation(
    automation: dict[str, Any],
    *,
    trigger_type: str,
    trigger_payload: dict[str, Any] | None = None,
    attempt: int = 0,
) -> None:
    """Execute an automation and persist run state."""
    from app.core.agent import run

    automation = _normalize_automation(automation)
    trigger_payload = trigger_payload or {}
    sb = get_supabase()
    started_at = _iso_now()

    queued_run = _upsert_automation_run(
        automation_id=automation["id"],
        user_id=automation.get("user_id", "default"),
        trigger_type=trigger_type,
        trigger_payload=trigger_payload,
        status="running",
        attempt=attempt,
        started_at=started_at,
    )
    await _publish_run_event("automation_runs.changed", queued_run, automation)

    logger.info("Running automation %s (%s)", automation["id"], automation.get("name"))

    try:
        result = await run(
            user_message=automation["prompt"],
            user_id=automation.get("user_id", "default"),
            conversation_id=None,
        )

        finished_at = _iso_now()
        completed_run = _upsert_automation_run(
            run_id=queued_run["id"],
            automation_id=automation["id"],
            user_id=automation.get("user_id", "default"),
            trigger_type=trigger_type,
            trigger_payload=trigger_payload,
            status="succeeded",
            attempt=attempt,
            result_summary=result.text[:500],
            started_at=started_at,
            finished_at=finished_at,
        )

        sb.table("automations").update(
            {
                "last_run": finished_at,
                "last_status": "succeeded",
                "last_error": None,
            }
        ).eq("id", automation["id"]).execute()

        await _publish_run_event("automation_runs.changed", completed_run, automation)
        await event_bus.publish(
            "automations.changed",
            {
                "action": "run_completed",
                "automation_id": automation["id"],
                "last_status": "succeeded",
            },
            user_id=automation.get("user_id", "default"),
            topics={"automations"},
        )
    except Exception as exc:
        logger.exception("Automation %s failed", automation["id"])
        finished_at = _iso_now()
        max_retries = int(automation.get("max_retries", 2) or 0)
        retry_delay = int(automation.get("retry_delay_seconds", 60) or 60)
        should_retry = attempt < max_retries
        next_retry_at = (_utcnow() + timedelta(seconds=retry_delay)).isoformat() if should_retry else None
        failed_status = "retry_scheduled" if should_retry else "failed"

        failed_run = _upsert_automation_run(
            run_id=queued_run["id"],
            automation_id=automation["id"],
            user_id=automation.get("user_id", "default"),
            trigger_type=trigger_type,
            trigger_payload=trigger_payload,
            status=failed_status,
            attempt=attempt,
            error=str(exc),
            started_at=started_at,
            finished_at=finished_at,
            next_retry_at=next_retry_at,
        )

        sb.table("automations").update(
            {
                "last_run": finished_at,
                "last_status": failed_status,
                "last_error": str(exc),
            }
        ).eq("id", automation["id"]).execute()

        await _publish_run_event("automation_runs.changed", failed_run, automation)
        await event_bus.publish(
            "automations.changed",
            {
                "action": "run_failed",
                "automation_id": automation["id"],
                "last_status": failed_status,
                "last_error": str(exc),
            },
            user_id=automation.get("user_id", "default"),
            topics={"automations"},
        )

        if should_retry:
            asyncio.create_task(
                _retry_after_delay(
                    automation=automation,
                    trigger_type=trigger_type,
                    trigger_payload=trigger_payload,
                    attempt=attempt + 1,
                    delay_seconds=retry_delay,
                )
            )


async def _retry_after_delay(
    *,
    automation: dict[str, Any],
    trigger_type: str,
    trigger_payload: dict[str, Any],
    attempt: int,
    delay_seconds: int,
) -> None:
    await asyncio.sleep(delay_seconds)
    await _execute_automation(
        automation,
        trigger_type=trigger_type,
        trigger_payload=trigger_payload,
        attempt=attempt,
    )


async def dispatch_platform_event(event_type: str, user_id: str, payload: dict[str, Any]) -> None:
    """Trigger event-driven automations."""
    matching = [
        automation
        for automation in event_automations.values()
        if automation.get("enabled")
        and automation.get("user_id", "default") == user_id
        and _event_matches(automation, event_type)
    ]

    for automation in matching:
        asyncio.create_task(
            _execute_automation(
                automation,
                trigger_type="event",
                trigger_payload={"event_type": event_type, **payload},
            )
        )


async def load_automations() -> None:
    """Load all enabled automations from DB and schedule them."""
    sb = get_supabase()
    result = sb.table("automations").select("*").eq("enabled", True).execute()
    event_automations.clear()

    for auto in result.data:
        try:
            await upsert_automation_runtime(auto)
        except Exception as exc:
            logger.error("Failed to load automation %s: %s", auto.get("name"), exc)


def start_scheduler() -> None:
    """Start the scheduler."""
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    """Stop the scheduler."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


async def upsert_automation_runtime(auto: dict[str, Any]) -> dict[str, Any]:
    """Ensure automation is registered in the correct runtime."""
    auto = _normalize_automation(auto)
    remove_automation_runtime(auto["id"])

    if not auto.get("enabled", True):
        return auto

    if auto["trigger_type"] == "event":
        event_automations[auto["id"]] = auto
        logger.info("Registered event automation %s", auto["name"])
    else:
        cron_kwargs = _parse_cron(auto["cron_expression"])
        scheduler.add_job(
            _execute_automation,
            trigger=CronTrigger(**cron_kwargs),
            kwargs={
                "automation": auto,
                "trigger_type": "cron",
                "trigger_payload": {"cron_expression": auto["cron_expression"]},
            },
            id=auto["id"],
            replace_existing=True,
            name=auto["name"],
        )
        logger.info("Scheduled automation %s (%s)", auto["name"], auto["cron_expression"])

    return auto


def remove_automation_runtime(automation_id: str) -> None:
    """Remove scheduled or event-based automation from memory."""
    event_automations.pop(automation_id, None)
    try:
        scheduler.remove_job(automation_id)
    except Exception:
        pass


async def add_automation_job(
    automation_id: str,
    user_id: str,
    name: str,
    cron_expression: str,
    prompt: str,
    *,
    trigger_type: str = "cron",
    trigger_config: dict[str, Any] | None = None,
    enabled: bool = True,
    max_retries: int = 2,
    retry_delay_seconds: int = 60,
) -> None:
    """Backward-compatible wrapper used by routers."""
    await upsert_automation_runtime(
        {
            "id": automation_id,
            "user_id": user_id,
            "name": name,
            "cron_expression": cron_expression,
            "prompt": prompt,
            "trigger_type": trigger_type,
            "trigger_config": trigger_config or {},
            "enabled": enabled,
            "max_retries": max_retries,
            "retry_delay_seconds": retry_delay_seconds,
        }
    )


def remove_automation_job(automation_id: str) -> None:
    """Backward-compatible wrapper used by routers."""
    remove_automation_runtime(automation_id)


async def list_automation_runs(user_id: str, automation_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    sb = get_supabase()
    query = sb.table("automation_runs").select("*").eq("user_id", user_id)
    if automation_id:
        query = query.eq("automation_id", automation_id)
    result = query.order("created_at", desc=True).limit(limit).execute()
    return result.data
