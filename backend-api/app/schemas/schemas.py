
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# Base schema for a Movie/Show - used for registering and viewing data
class MovieShowBase(BaseModel):
    tmdb_id: int = Field(..., description="The unique ID from The Movie Database (TMDB).", example=123)


# Schema for registering a new movie (R1.5)
class MovieShowCreate(MovieShowBase):
    pass  # Currently only requires tmdb_id


# Schema for the event message sent to RabbitMQ (R1.1, R1.2)
class MovieShowEvent(MovieShowBase):
    event_type: str = Field(..., description="Type of event: 'VIEW' or 'EXTERNAL_UPDATE'.", example="VIEW")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Schema for the response object (R1.3, R1.4)
class MovieShowResponse(MovieShowBase):
    title: str = Field(..., example="The Big Lebowski")
    internal_views_count: int = Field(..., example=42)
    external_score: float = Field(..., example=8.1)
    final_trend_score: float = Field(..., example=8.5)
    last_updated_at: datetime

    # Configuration class for Pydantic
    class Config:
        from_attributes = True  # Allows Pydantic to read ORM objects directly



# Schema for the incoming view event from the Frontend (R1.1)
class MovieShowViewRequest(BaseModel):
    tmdb_id: int = Field(..., description="The TMDB ID of the movie being viewed.", example=123)