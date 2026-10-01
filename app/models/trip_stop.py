from sqlalchemy import ForeignKey, Integer, DateTime
from app.database import AsyncBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

class TripStop(AsyncBase):
    __tablename__ = "trip_stops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), nullable=False)
    stop_number: Mapped[int] = mapped_column(Integer, nullable=False)
    arrival_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    departure_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    trip: Mapped["Trip"] = relationship("Trip", back_populates="stops")     # type: ignore
    city: Mapped["City"] = relationship("City", back_populates="stops")     # type: ignore
    departing_tickets: Mapped[list["Ticket"]] = relationship("Ticket", foreign_keys="Ticket.departure_stop_id", back_populates="departure_stop")     # type: ignore
    arriving_tickets: Mapped[list["Ticket"]] = relationship("Ticket", foreign_keys="Ticket.arrival_stop_id", back_populates="arrival_stop")     # type: ignore