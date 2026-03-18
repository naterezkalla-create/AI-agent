"""APScheduler setup — runs CRON jobs that trigger the agent."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.memory.supabase_client import get_supabase

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_automation(automation_id: str, prompt: str):
    """Execute an automation by sending its prompt through the agent loop."""
    from app.core.agent import run
    from datetime import datetime, timezone

    logger.info(f"Running automation {automation_id}: {prompt[:100]}")
    try:
        result = await run(
            user_message=prompt,
            user_id="default",
            conversation_id=None,  # Each run creates a new conversation
        )
        logger.info(f"Automation {automation_id} completed: {result.text[:200]}")

        # Update last_run timestamp
        sb = get_supabase()
        sb.table("automations").update({
            "last_run": datetime.now(timezone.utc).isoformat(),
        }).eq("id", automation_id).execute()

    except Exception as e:
        logger.error(f"Automation {automation_id} failed: {e}")


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


async def load_automations():
    """Load all enabled automations from DB and schedule them."""
    sb = get_supabase()
    result = sb.table("automations").select("*").eq("enabled", True).execute()

    for auto in result.data:
        try:
            cron_kwargs = _parse_cron(auto["cron_expression"])
            scheduler.add_job(
                _run_automation,
                trigger=CronTrigger(**cron_kwargs),
                args=[auto["id"], auto["prompt"]],
                id=auto["id"],
                replace_existing=True,
                name=auto["name"],
            )
            logger.info(f"Scheduled automation: {auto['name']} ({auto['cron_expression']})")
        except Exception as e:
            logger.error(f"Failed to schedule automation {auto['name']}: {e}")


def start_scheduler():
    """Start the scheduler."""
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """Stop the scheduler."""
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


async def add_automation_job(automation_id: str, name: str, cron_expression: str, prompt: str):
    """Add or update a scheduled job."""
    cron_kwargs = _parse_cron(cron_expression)
    scheduler.add_job(
        _run_automation,
        trigger=CronTrigger(**cron_kwargs),
        args=[automation_id, prompt],
        id=automation_id,
        replace_existing=True,
        name=name,
    )


def remove_automation_job(automation_id: str):
    """Remove a scheduled job."""
    try:
        scheduler.remove_job(automation_id)
    except Exception:
        pass  # Job may not exist
