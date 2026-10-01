from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.trip import Trip
from fastapi import HTTPException

from app.database import get_db
from app.models.users import User
from app.schemas.carriage import CarriageCreate, CarriageResponse, CarriageUpdate
from app.models.carriage import Carriage
from app.security import require_moderator

router = APIRouter(prefix="/carriages", tags=["Carriages"])

@router.post("/", response_model=CarriageResponse,status_code=status.HTTP_201_CREATED)
async def create_carriage(carriage: CarriageCreate, db: AsyncSession = Depends(get_db), current_user: User =Depends(require_moderator)):
    trip = await db.get(Trip, carriage.trip_id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    existing_carriage = await db.execute(select(Carriage).where(Carriage.trip_id == carriage.trip_id, Carriage.number == carriage.number))
    existing_carriage = existing_carriage.scalars().first()
    if existing_carriage:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Carriage with this trip_id and number already exists")
    
    new_carriage = Carriage(**carriage.model_dump())
    db.add(new_carriage)
    await db.commit()
    await db.refresh(new_carriage)
    return new_carriage

@router.get("/", response_model=list[CarriageResponse])
async def get_all_carriages(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_moderator)):
    result = await db.execute(select(Carriage))
    carriages = result.scalars().all()
    return carriages

@router.get("/{carriage_id}", response_model=CarriageResponse)
async def get_carriage(carriage_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_moderator)):
    result = await db.execute(select(Carriage).where(Carriage.id == carriage_id))
    carriage = result.scalars().first()
    if not carriage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carriage not found")
    return carriage

@router.patch("/{carriage_id}", response_model=CarriageResponse)
async def update_carriage(carriage_id: int, carriage: CarriageUpdate, db: AsyncSession = Depends(get_db), current_user: User =Depends(require_moderator)):
    result = await db.execute(select(Carriage).where(Carriage.id == carriage_id))
    existing_carriage = result.scalars().first()
    if not existing_carriage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carriage not found")
    updated_data = carriage.model_dump(exclude_unset=True)
    if "number" in updated_data:
        existing_carriage_with_number = await db.execute(
            select(Carriage).where(
                Carriage.trip_id == existing_carriage.trip_id,
                Carriage.number == updated_data["number"],
                Carriage.id != carriage_id
            )
        )
        if existing_carriage_with_number.scalars().first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Carriage with this trip_id and number already exists")
    for key, value in updated_data.items():
        setattr(existing_carriage, key, value)
    await db.commit()
    await db.refresh(existing_carriage)
    return existing_carriage

@router.delete("/{carriage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_carriage(carriage_id: int, db: AsyncSession = Depends(get_db), current_user: User =Depends(require_moderator)):
    result = await db.execute(select(Carriage).where(Carriage.id == carriage_id))
    existing_carriage = result.scalars().first()
    if not existing_carriage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carriage not found")
    await db.delete(existing_carriage)
    await db.commit()