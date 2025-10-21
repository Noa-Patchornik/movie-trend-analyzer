# movie-trend-analyzer/backend-api/app/main.py
import sys
sys.stdout.reconfigure(line_buffering=True)

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .db.database import engine, Base, get_db
from .db import models
from . import messaging
from .api import movies

# Create all tables defined in models.py in the database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Movie Trend Analyzer API",
    description="API for registering views and triggering external score updates.",
    version="1.0.0",
)

# Include the router for movie-related endpoints
app.include_router(movies.router, prefix="/api/movies", tags=["movies"])

# Basic health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}
