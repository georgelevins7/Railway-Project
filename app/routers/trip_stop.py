from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.database import get_db
from app.models.cities import City
from app.models.trip import Trip
from app.models.users import User
from app.schemas.trip_stop import TripStopCreate, TripStopResponse, TripStopUpdate
from app.models.trip_stop import TripStop
from app.security import require_moderator

router = APIRouter(prefix="/stops", tags=["Stops"])


async def validate_stop_query(trip_id: int, stop_number: int, db: AsyncSession, arrival_time, departure_time, exclude_stop_id: int | None = None):
    previous_stop = await db.execute(select(TripStop).where(TripStop.trip_id == trip_id, 
                                                            TripStop.stop_number < stop_number, 
                                                            TripStop.id != exclude_stop_id).
                                                            order_by(TripStop.stop_number.desc()))
    previous_stop = previous_stop.scalars().first()

    next_stop = await db.execute(select(TripStop).where(TripStop.trip_id == trip_id, 
                                                        TripStop.stop_number > stop_number,
                                                        TripStop.id != exclude_stop_id).
                                                        order_by(TripStop.stop_number))
    next_stop = next_stop.scalars().first()
    if previous_stop and not arrival_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arrival time is required for this stop")

    if previous_stop and not previous_stop.departure_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Previous stop's departure time is required for this stop")

    if previous_stop and arrival_time and previous_stop.departure_time:
        if arrival_time <= previous_stop.departure_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arrival time cannot be earlier than the previous stop's departure time")
    if next_stop and not departure_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Departure time is required for this stop")

    if next_stop and not next_stop.arrival_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Next stop's arrival time is required for this stop")

    if next_stop and departure_time and next_stop.arrival_time:
        if departure_time >= next_stop.arrival_time:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Departure time cannot be later than the next stop's arrival time")

@router.post("/", response_model=TripStopResponse, status_code=status.HTTP_201_CREATED)
async def create_trip_stop(trip_stop: TripStopCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_moderator)):
    trip = await db.get(Trip, trip_stop.trip_id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    city = await db.get(City, trip_stop.city_id)
    if not city:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")
    existing_trip_stop = await db.execute(select(TripStop).where(TripStop.trip_id == trip_stop.trip_id, TripStop.city_id == trip_stop.city_id))
    existing_trip_stop = existing_trip_stop.scalars().first()
    if existing_trip_stop:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip stop already exists")

    existing_stop_number = await db.execute(select(TripStop).where(TripStop.trip_id == trip_stop.trip_id, TripStop.stop_number == trip_stop.stop_number))
    existing_stop_number = existing_stop_number.scalars().first()
    if existing_stop_number:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stop number already exists for this trip")
    
    await validate_stop_query(trip_id = trip_stop.trip_id, 
                              stop_number=trip_stop.stop_number,
                              departure_time=trip_stop.departure_time, 
                              arrival_time=trip_stop.arrival_time,
                              db=db)
    new_trip_stop = TripStop(**trip_stop.model_dump())
    db.add(new_trip_stop)
    await db.commit()
    await db.refresh(new_trip_stop)
    return new_trip_stop

@router.get("/", response_model=list[TripStopResponse])
async def get_all_trip_stops(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TripStop))
    trip_stops = result.scalars().all()
    return trip_stops

@router.get("/{trip_stop_id}", response_model=TripStopResponse)
async def get_trip_stop(trip_stop_id: int, db: AsyncSession = Depends(get_db)):
    trip_stop = await db.get(TripStop, trip_stop_id)
    if not trip_stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip stop not found")
    return trip_stop

@router.patch("/{trip_stop_id}", response_model=TripStopResponse)
async def update_trip_stop(trip_stop_id: int, trip_stop: TripStopUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_moderator)):
    existing_trip_stop = await db.get(TripStop, trip_stop_id)
    updated_data = trip_stop.model_dump(exclude_unset=True)
    if not existing_trip_stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip stop not found")

    arrival_time = updated_data.get("arrival_time", existing_trip_stop.arrival_time)
    departure_time = updated_data.get("departure_time", existing_trip_stop.departure_time)
    stop_number = updated_data.get("stop_number", existing_trip_stop.stop_number)

    if arrival_time and departure_time and arrival_time >= departure_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arrival time cannot be later than departure time")
    
    if "city_id" in updated_data:
        city = await db.get(City, updated_data.get("city_id"))
        if not city:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")

        same_city_trip_stop = await db.execute(select(TripStop).where(TripStop.trip_id == existing_trip_stop.trip_id,
                                                                    TripStop.city_id == updated_data.get("city_id"),
                                                                    TripStop.id != trip_stop_id
            )
        )
        same_city_trip_stop = same_city_trip_stop.scalars().first()
        if same_city_trip_stop:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip stop with the same city already exists for this trip")

    if "stop_number" in updated_data:
        same_stop_number_trip_stop = await db.execute(select(TripStop).where(TripStop.trip_id == existing_trip_stop.trip_id,
                                                                             TripStop.stop_number == updated_data.get("stop_number"),
                                                                             TripStop.id != trip_stop_id
            )
        )
        same_stop_number_trip_stop = same_stop_number_trip_stop.scalars().first()
        if same_stop_number_trip_stop:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stop number already exists for this trip")


    await validate_stop_query(trip_id=existing_trip_stop.trip_id, 
                              stop_number=stop_number,
                              arrival_time=arrival_time,
                              departure_time=departure_time,
                              db=db,
                              exclude_stop_id=existing_trip_stop.id)
    for key, value in updated_data.items():
        setattr(existing_trip_stop, key, value)

    await db.commit()
    await db.refresh(existing_trip_stop)
    return existing_trip_stop

@router.delete("/{trip_stop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip_stop(trip_stop_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_moderator)):
    trip_stop = await db.get(TripStop, trip_stop_id)
    if not trip_stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip stop not found")
    await db.delete(trip_stop)
    await db.commit()