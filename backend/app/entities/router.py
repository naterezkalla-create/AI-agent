from typing import Optional
from fastapi import APIRouter, HTTPException
from app.entities.models import EntityCreate, EntityUpdate
from app.entities import crud

router = APIRouter(prefix="/entities", tags=["entities"])


@router.post("/")
async def create_entity(body: EntityCreate):
    entity = await crud.create_entity("default", body.type, body.data)
    return entity


@router.get("/")
async def list_entities(entity_type: Optional[str] = None, limit: int = 50):
    return await crud.list_entities("default", entity_type, limit)


@router.get("/{entity_id}")
async def get_entity(entity_id: str):
    entity = await crud.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.patch("/{entity_id}")
async def update_entity(entity_id: str, body: EntityUpdate):
    entity = await crud.update_entity(entity_id, body.data)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.delete("/{entity_id}")
async def delete_entity(entity_id: str):
    success = await crud.delete_entity(entity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"deleted": True}
