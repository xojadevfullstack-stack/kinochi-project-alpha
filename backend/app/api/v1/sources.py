from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_admin
from app.infrastructure.db.repositories.source_repository import SourceRepository
from app.domain.series.source_entities import SourceResponse, SourceCreate, SourceUpdate

router = APIRouter()

@router.get("/", response_model=List[SourceResponse])
async def get_sources(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin)
):
    repo = SourceRepository(db)
    return await repo.get_all_sources()

@router.post("/", response_model=SourceResponse)
async def create_source(
    data: SourceCreate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin)
):
    repo = SourceRepository(db)
    return await repo.create_source(data.model_dump())

@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    data: SourceUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin)
):
    repo = SourceRepository(db)
    source = await repo.update_source(source_id, data.model_dump(exclude_unset=True))
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source

@router.delete("/{source_id}")
async def delete_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin)
):
    repo = SourceRepository(db)
    deleted = await repo.delete_source(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"ok": True}
