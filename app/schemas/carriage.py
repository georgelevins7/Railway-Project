from pydantic import BaseModel, Field


class CarriageCreate(BaseModel):
    trip_id: int = Field(gt=0)
    number: int = Field(gt=0)
    capacity: int = Field(gt=0, le=40)

class CarriageUpdate(BaseModel):
    number: int | None = Field(gt=0, default=None)
    capacity: int | None = Field(gt=0, le=40, default=None)

class CarriageResponse(BaseModel):
    id: int
    trip_id: int
    number: int
    capacity: int

    class Config:
        from_attributes = True