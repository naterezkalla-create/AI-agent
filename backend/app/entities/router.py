from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.entities.models import EntityCreate, EntityUpdate
from app.entities import crud
from app.automations.scheduler import dispatch_platform_event
from app.events.bus import event_bus

router = APIRouter(prefix="/entities", tags=["entities"])


@router.post("/")
async def create_entity(body: EntityCreate, user_id: str = Depends(get_current_user)):
    entity = await crud.create_entity(user_id, body.type, body.data)
    await event_bus.publish(
        "entities.changed",
        {"action": "created", "entity_id": entity["id"], "entity_type": entity["type"]},
        topics={"entities"},
    )
    await dispatch_platform_event(
        "entities.changed",
        user_id,
        {"action": "created", "entity_id": entity["id"], "entity_type": entity["type"]},
    )
    return entity


@router.get("/")
async def list_entities(entity_type: Optional[str] = None, limit: int = 50, user_id: str = Depends(get_current_user)):
    return await crud.list_entities(user_id, entity_type, limit)


@router.get("/{entity_id}")
async def get_entity(entity_id: str, user_id: str = Depends(get_current_user)):
    entity = await crud.get_entity(entity_id, user_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.patch("/{entity_id}")
async def update_entity(entity_id: str, body: EntityUpdate, user_id: str = Depends(get_current_user)):
    entity = await crud.update_entity(entity_id, user_id, body.data)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    await event_bus.publish(
        "entities.changed",
        {"action": "updated", "entity_id": entity["id"], "entity_type": entity["type"]},
        topics={"entities"},
    )
    await dispatch_platform_event(
        "entities.changed",
        user_id,
        {"action": "updated", "entity_id": entity["id"], "entity_type": entity["type"]},
    )
    return entity


@router.delete("/{entity_id}")
async def delete_entity(entity_id: str, user_id: str = Depends(get_current_user)):
    success = await crud.delete_entity(entity_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entity not found")
    await event_bus.publish(
        "entities.changed",
        {"action": "deleted", "entity_id": entity_id},
        topics={"entities"},
    )
    await dispatch_platform_event(
        "entities.changed",
        user_id,
        {"action": "deleted", "entity_id": entity_id},
    )
    return {"deleted": True}
