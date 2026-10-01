from pydantic import BaseModel, Field

class TripCreate(BaseModel):
    number: int = Field(gt=0, description="Trip number must be a positive integer")

class TripUpdate(BaseModel):
    is_active: bool | None = Field(default=None)

class TripResponse(BaseModel):
    id: int
    number: int
    is_active: bool

    class Config:
        from_attributes = True