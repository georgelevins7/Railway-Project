from pydantic import BaseModel, Field

class CityCreate(BaseModel):
    name: str = Field(min_length=3, max_length=50, description="City name must be between 3 and 50 characters long")

class CityResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

