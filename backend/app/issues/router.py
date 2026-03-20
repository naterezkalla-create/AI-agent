"""Issue and suggestion API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.issues.service import (
    approve_suggestion,
    generate_suggestions_for_user,
    list_automation_suggestions,
    list_issues,
    reject_suggestion,
    resolve_issue,
    scan_user_issues,
)

router = APIRouter(prefix="/api/issues", tags=["issues"])


@router.get("/")
async def get_issues(status: str | None = None, user_id: str = Depends(get_current_user)):
    return await list_issues(user_id, status=status)


@router.post("/scan")
async def scan_issues(user_id: str = Depends(get_current_user)):
    return await scan_user_issues(user_id)


@router.patch("/{issue_id}")
async def update_issue(issue_id: str, body: dict, user_id: str = Depends(get_current_user)):
    status = body.get("status")
    if status not in {"open", "resolved", "dismissed"}:
        raise HTTPException(status_code=400, detail="Invalid issue status")
    issue = await resolve_issue(issue_id, user_id, status=status)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.get("/suggestions")
async def get_suggestions(status: str | None = None, user_id: str = Depends(get_current_user)):
    return await list_automation_suggestions(user_id, status=status)


@router.post("/suggestions/generate")
async def generate_suggestions(user_id: str = Depends(get_current_user)):
    return await generate_suggestions_for_user(user_id)


@router.post("/suggestions/{suggestion_id}/approve")
async def approve_automation_suggestion(suggestion_id: str, user_id: str = Depends(get_current_user)):
    suggestion = await approve_suggestion(suggestion_id, user_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return suggestion


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_automation_suggestion(suggestion_id: str, user_id: str = Depends(get_current_user)):
    suggestion = await reject_suggestion(suggestion_id, user_id)
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return suggestion
