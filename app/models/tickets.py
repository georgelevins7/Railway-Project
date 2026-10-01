from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func, Numeric
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import AsyncBase
from datetime import datetime


class Ticket(AsyncBase):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False)
    carriage_id: Mapped[int] = mapped_column(ForeignKey("carriages.id"), nullable=False)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)

    departure_stop_id: Mapped[int] = mapped_column(ForeignKey("trip_stops.id"), nullable=False)
    arrival_stop_id: Mapped[int] = mapped_column(ForeignKey("trip_stops.id"), nullable=False)

    passenger_name: Mapped[str] = mapped_column(String(30), nullable=False)
    passenger_surname: Mapped[str] = mapped_column(String(30), nullable=False)
    passenger_passport: Mapped[str] = mapped_column(String(30), nullable=False)

    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="tickets")     # type: ignore
    trip: Mapped["Trip"] = relationship("Trip", back_populates="tickets")     # type: ignore
    carriage: Mapped["Carriage"] = relationship("Carriage", back_populates="tickets")     # type: ignore
    
    departure_stop: Mapped["TripStop"] = relationship("TripStop", foreign_keys=[departure_stop_id], back_populates="departing_tickets")     # type: ignore
    arrival_stop: Mapped["TripStop"] = relationship("TripStop", foreign_keys=[arrival_stop_id], back_populates="arriving_tickets")     # type: ignore