from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime

class TicketCreate(BaseModel):
    trip_id: int = Field(gt=0)
    departure_city_id: int = Field(gt=0)
    arrival_city_id: int = Field(gt=0)
    carriage_id: int = Field(gt=0)
    seat_number: int = Field(gt=0)
    passenger_name: str = Field(min_length=3, max_length=30)
    passenger_surname: str = Field(min_length=3, max_length=30)
    passenger_passport: str = Field(min_length=11, max_length=11)

    @model_validator(mode="before")
    def check_cities(cls, values):
        departure_city_id = values.get("departure_city_id")
        arrival_city_id = values.get("arrival_city_id")
        if departure_city_id and arrival_city_id and departure_city_id == arrival_city_id:
            raise ValueError("Departure and arrival cities must be different")
        return values

    @field_validator("passenger_name")
    def name_must_be_alpha(cls, value):
        if not value.isalpha():
            raise ValueError("Passenger name must contain only alphabetic characters")
        return value
    @field_validator("passenger_surname")
    def surname_must_be_alpha(cls, value):
        if not value.isalpha():
            raise ValueError("Passenger surname must contain only alphabetic characters")
        return value


    @field_validator("passenger_passport")
    def passport_must_be_numeric(cls, value):
        if not value.isdigit():
            raise ValueError("Passenger passport must contain only numeric characters")
        return value



class TicketResponse(BaseModel):
    ticket_number: int
    trip_id: int
    departure_city: str
    arrival_city: str
    carriage_number: int
    seat_number: int
    passenger_name: str
    passenger_surname: str
    passenger_passport: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True