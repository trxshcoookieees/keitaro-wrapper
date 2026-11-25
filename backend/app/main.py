from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine
from app.api.keitaro import router as keitaro_router

app = FastAPI(title="Keitaro API")
app.include_router(keitaro_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Keitaro API is running✅"}


@app.get("/health/db")
async def check_database():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

    return {"database": "connected", "result": result.scalar()}