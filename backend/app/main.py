from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine
from app.api.keitaro import router as keitaro_router

app = FastAPI(title="Keitaro API")
app.include_router(keitaro_router)

@app.get("/")
async def root():
    return {"message": "Keitaro API is running✅"}


@app.get("/health/db")
async def check_database():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

    return {"database": "connected", "result": result.scalar()}