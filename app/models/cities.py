from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import AsyncBase


class City(AsyncBase):
    __tablename__ = "cities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    stops: Mapped[list["TripStop"]] = relationship("TripStop", back_populates="city")     # type: ignore