from pydantic import BaseModel, Field, model_validator
from datetime import datetime

class TripStopCreate(BaseModel):
    trip_id: int = Field(gt=0)
    city_id: int = Field(gt=0)
    stop_number: int = Field(gt=0)
    departure_time: datetime | None = None
    arrival_time: datetime | None = None

    @model_validator(mode="before")
    def check_times(cls, values):
        departure_time = values.get("departure_time")
        arrival_time = values.get("arrival_time")
        if departure_time and arrival_time and arrival_time >= departure_time:
            raise ValueError("Departure time must be after arrival time")
        return values

class TripStopUpdate(BaseModel):
    city_id: int | None = Field(gt=0, default=None)
    stop_number: int | None = Field(gt=0, default=None)
    departure_time: datetime | None = None
    arrival_time: datetime | None = None

    @model_validator(mode="before")
    def check_times(cls, values):
        departure_time = values.get("departure_time")
        arrival_time = values.get("arrival_time")
        if departure_time and arrival_time and arrival_time >= departure_time:
            raise ValueError("Departure time must be after arrival time")
        return values

class TripStopResponse(BaseModel):
    id: int
    trip_id: int
    city_id: int
    stop_number: int
    departure_time: datetime | None
    arrival_time: datetime | None

    class Config:
        from_attributes = True