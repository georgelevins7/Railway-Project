from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import AsyncBase


class Carriage(AsyncBase):
    __tablename__ = "carriages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    trip: Mapped["Trip"] = relationship("Trip", back_populates="carriages")     # type: ignore
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="carriage")     # type: ignore
