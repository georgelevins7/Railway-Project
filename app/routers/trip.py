from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.database import get_db
from app.models.users import User
from app.schemas.trip import TripCreate, TripResponse, TripUpdate
from app.models.trip import Trip
from app.security import require_moderator

router = APIRouter(prefix="/trips", tags=["Trips"])

@router.post("/", response_model=TripResponse,status_code=status.HTTP_201_CREATED)
async def create_trip(trip: TripCreate, db: AsyncSession = Depends(get_db), current_user: User =Depends(require_moderator)):
    new_trip = Trip(**trip.model_dump())
    db.add(new_trip)
    await db.commit()
    await db.refresh(new_trip)
    return new_trip

@router.get("/", response_model=list[TripResponse])
async def get_all_trips(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trip))
    trips = result.scalars().all()
    return trips

@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = result.scalars().first()
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip

@router.patch("/{trip_id}", response_model=TripResponse)
async def update_trip(trip_id: int, trip: TripUpdate, db: AsyncSession = Depends(get_db), current_user: User =Depends(require_moderator)):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    existing_trip = result.scalars().first()
    if not existing_trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    for key, value in trip.model_dump(exclude_unset=True).items():
        setattr(existing_trip, key, value)
    await db.commit()
    await db.refresh(existing_trip)
    return existing_trip

@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(trip_id: int, db: AsyncSession = Depends(get_db), current_user: User =Depends(require_moderator)):
    result = await db.execute(select(Trip).where(Trip.id == trip_id))
    existing_trip = result.scalars().first()
    if not existing_trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    await db.delete(existing_trip)
    await db.commit()