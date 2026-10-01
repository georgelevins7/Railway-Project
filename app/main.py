from fastapi import FastAPI
from app.routers import trip_stop, trip, cities, users, carriage
import app.models

app = FastAPI(
    title="Railway Project",
    description="API for managing railway trips, stops, cities, users, carriages, and tickets",
    version="1.0.0",
)

app.include_router(trip_stop.router)
app.include_router(trip.router)
app.include_router(cities.router)
app.include_router(users.router)
app.include_router(carriage.router)