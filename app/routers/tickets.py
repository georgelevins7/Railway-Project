from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.database import get_db
from app.models.users import User
from app.schemas.tickets import TicketCreate, TicketResponse
from app.models.tickets import Ticket
from app.models.trip import Trip
from app.models.carriage import Carriage
from app.models.trip_stop import TripStop
from app.models.cities import City
from app.security import get_current_user, require_moderator
import uuid


router = APIRouter(prefix="/tickets", tags=["tickets"])

async def ticket_response(ticket: Ticket, db: AsyncSession):
    trip = await db.get(Trip, ticket.trip_id)
    departure_stop = await db.get(TripStop, ticket.departure_stop_id)
    arrival_stop = await db.get(TripStop, ticket.arrival_stop_id)
    departure_city = await db.get(City, departure_stop.city_id)
    arrival_city = await db.get(City, arrival_stop.city_id)
    carriage = await db.get(Carriage, ticket.carriage_id)

    return TicketResponse(
        ticket_number=ticket.ticket_number,
        train_number=trip.number,
        departure_city=departure_city.name,
        arrival_city=arrival_city.name,
        departure_time=departure_stop.departure_time,
        arrival_time=arrival_stop.arrival_time,
        carriage_number=carriage.number,
        seat_number=ticket.seat_number,
        passenger_name=ticket.passenger_name,
        passenger_surname=ticket.passenger_surname,
        passenger_passport=ticket.passenger_passport,
        price=ticket.price,
        created_at=ticket.created_at,
        is_active=ticket.is_active
    )

@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(ticket: TicketCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    trip = await db.get(Trip, ticket.trip_id)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    if trip.is_active is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trip is not active")
    
    departure_stop = await db.execute(select(TripStop).where(TripStop.city_id == ticket.departure_city_id, 
                                                             TripStop.trip_id == ticket.trip_id))
    departure_stop = departure_stop.scalars().first()
    if not departure_stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Departure stop not found")

    arrival_stop = await db.execute(select(TripStop).where(TripStop.city_id == ticket.arrival_city_id, 
                                                             TripStop.trip_id == ticket.trip_id))
    arrival_stop = arrival_stop.scalars().first()
    if not arrival_stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arrival stop not found")

    if departure_stop.stop_number >= arrival_stop.stop_number:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Departure stop must be before arrival stop")

    carriage = await db.get(Carriage, ticket.carriage_id)
    if not carriage:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carriage not found")

    if carriage.trip_id != ticket.trip_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Carriage does not belong to the specified trip")

    seat_number = ticket.seat_number
    if seat_number < 1 or seat_number > carriage.capacity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid seat number")

    existing_tickets = await db.execute(select(Ticket).where(Ticket.trip_id == ticket.trip_id,
                                                             Ticket.is_active == True,
                                                             Ticket.carriage_id == ticket.carriage_id, 
                                                             Ticket.seat_number == ticket.seat_number))
    existing_tickets = existing_tickets.scalars().all()

    for existing_ticket in existing_tickets:
        existing_departure_stop = await db.get(TripStop, existing_ticket.departure_stop_id)
        existing_arrival_stop = await db.get(TripStop, existing_ticket.arrival_stop_id)

        if (existing_departure_stop.stop_number < arrival_stop.stop_number and
             existing_arrival_stop.stop_number > departure_stop.stop_number):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat already booked for the selected segment")

    segments = arrival_stop.stop_number - departure_stop.stop_number
    price_per_segment = 20
    ticket_price = segments * price_per_segment

    ticket_number = uuid.uuid4().hex[:10].upper()
    
    new_ticket = Ticket(ticket_number=ticket_number, 
                        user_id=current_user.id, 
                        trip_id=ticket.trip_id,
                        carriage_id=ticket.carriage_id,
                        departure_stop_id=departure_stop.id,
                        arrival_stop_id=arrival_stop.id,
                        seat_number=ticket.seat_number,
                        passenger_name=ticket.passenger_name,
                        passenger_surname=ticket.passenger_surname,
                        passenger_passport=ticket.passenger_passport,
                        price=ticket_price)
    db.add(new_ticket)
    await db.commit()
    await db.refresh(new_ticket)
    return await ticket_response(new_ticket, db)

@router.get("/", response_model=list[TicketResponse])
async def get_all_tickets(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_moderator)):
    result = await db.execute(select(Ticket).where(Ticket.is_active == True))
    tickets = result.scalars().all()
    return [await ticket_response(ticket, db) for ticket in tickets]

@router.get("/my", response_model=list[TicketResponse])
async def get_my_tickets(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ticket).where(Ticket.user_id == current_user.id, Ticket.is_active == True))
    tickets = result.scalars().all()
    if not tickets:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tickets found")
    return [await ticket_response(ticket, db) for ticket in tickets]

@router.get("/{ticket_number}", response_model=TicketResponse)
async def get_ticket(ticket_number: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Ticket).where(Ticket.ticket_number == ticket_number, 
                                                   Ticket.is_active == True,
                                                   Ticket.user_id == current_user.id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return await ticket_response(ticket, db)

@router.patch("/{ticket_number}/cancel", response_model=TicketResponse)
async def cancel_ticket(ticket_number: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Ticket).where(Ticket.ticket_number == ticket_number, 
                                                   Ticket.is_active == True,
                                                   Ticket.user_id == current_user.id))
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    ticket.is_active = False
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return await ticket_response(ticket, db)