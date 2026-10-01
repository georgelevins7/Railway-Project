from sqlalchemy import Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import AsyncBase


class Trip(AsyncBase):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    stops: Mapped[list["TripStop"]] = relationship("TripStop", back_populates="trip")     # type: ignore    
    carriages: Mapped[list["Carriage"]] = relationship("Carriage", back_populates="trip")     # type: ignore
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="trip")     # type: ignore