from fastapi import APIRouter
from app.models.cities import City
from sqlalchemy import select
from app.database import get_db
from app.models.users import User
from app.schemas.cities import CityCreate, CityResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from app.security import require_moderator

router = APIRouter(prefix="/cities", tags=["cities"])
@router.post("/", response_model=CityResponse)
async def create_city(city: CityCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_moderator)):
    new_city = City(**city.model_dump())
    db.add(new_city)
    await db.commit()
    await db.refresh(new_city)
    return new_city

@router.get("/", response_model=list[CityResponse]) 
async def all_cities(db: AsyncSession = Depends(get_db)):
    cities = await db.execute(select(City))
    cities = cities.scalars().all()
    return cities

@router.get("/{city_id}", response_model=CityResponse)
async def get_city(city_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_moderator)):
    city = await db.execute(select(City).filter(City.id == city_id))
    city = city.scalars().first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    return city

@router.delete("/{city_id}", status_code=204)
async def delete_city(city_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_moderator)):
    city = await db.execute(select(City).filter(City.id == city_id))
    city = city.scalars().first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    await db.delete(city)
    await db.commit()
    return None