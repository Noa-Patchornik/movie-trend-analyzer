
import sys
sys.stdout.reconfigure(line_buffering=True)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db import models
from ..db.database import get_db
from ..schemas import schemas
from .. import messaging
from typing import List

router = APIRouter()


# --- Helpers ---

def get_movie_by_tmdb_id(db: Session, tmdb_id: int):
    """Fetches a movie record from the DB by its TMDB ID."""
    return db.query(models.MovieShow).filter(models.MovieShow.tmdb_id == tmdb_id).first()


# --- R1.5: Register New Movie ---

@router.post(
    "/register",
    response_model=schemas.MovieShowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new movie/show using its TMDB ID"
)
def register_movie(movie_data: schemas.MovieShowCreate, db: Session = Depends(get_db)):
    # 1. Check if movie already exists to prevent duplicates
    db_movie = get_movie_by_tmdb_id(db, movie_data.tmdb_id)
    if db_movie:
        # If it exists, we can return the existing one or raise an error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already registered."
        )

    # 2. Create the SQLAlchemy ORM object
    new_movie = models.MovieShow(tmdb_id=movie_data.tmdb_id, title=f"Placeholder Title for ID {movie_data.tmdb_id}")

    # 3. Add to session, commit to DB, and refresh to get the generated ID and timestamps
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)

    # 4. Trigger external update immediately (since we don't have the real title yet)
    # The External Worker will later fetch the real title and external score from TMDB
    event_message = schemas.MovieShowEvent(
        tmdb_id=movie_data.tmdb_id,
        event_type="INITIAL_EXTERNAL_UPDATE"
    )
    messaging.send_message(messaging.EXTERNAL_SCORE_UPDATE_QUEUE, event_message.model_dump())

    return new_movie


# --- R1.1: Register Internal View Event ---

@router.post(
    "/view",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Sends a view event to the Internal Worker"
)
def register_movie_view(view_data: schemas.MovieShowViewRequest, db: Session = Depends(get_db)):
    # 1. Check if the movie is registered in our local DB
    db_movie = get_movie_by_tmdb_id(db, view_data.tmdb_id)
    if not db_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found. Please register it first."
        )

    # 2. Construct the event message for the Internal Worker
    event_message = schemas.MovieShowEvent(
        tmdb_id=view_data.tmdb_id,
        event_type="VIEW"
    )

    # 3. Send the message to RabbitMQ (ASYNC operation)
    if not messaging.send_message(messaging.VIEW_EVENT_QUEUE, event_message.model_dump()):
        # Handle case where MQ connection failed
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Message queue service unavailable."
        )

    return {"message": "View event sent to queue for asynchronous processing."}


# --- R1.2: Trigger External Score Update ---

@router.post(
    "/trigger_external_update/{tmdb_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Triggers the External Worker to fetch TMDB data"
)
def trigger_external_update(tmdb_id: int, db: Session = Depends(get_db)):
    # 1. Check if movie exists
    if not get_movie_by_tmdb_id(db, tmdb_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movie not registered.")

    # 2. Construct the event message for the External Worker
    event_message = schemas.MovieShowEvent(
        tmdb_id=tmdb_id,
        event_type="EXTERNAL_UPDATE"
    )

    # 3. Send the message to RabbitMQ (ASYNC operation)
    if not messaging.send_message(messaging.EXTERNAL_SCORE_UPDATE_QUEUE, event_message.model_dump()):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Message queue service unavailable."
        )

    return {"message": f"External update event sent for TMDB ID {tmdb_id}."}


# --- R1.4 & R1.3: Get All Movies (and a single trend score) ---

@router.get(
    "",
    response_model=List[schemas.MovieShowResponse],
    summary="Get a list of all movies and their current trend scores"
)
def get_all_movies(db: Session = Depends(get_db)):
    # Simple select query to fetch all records
    movies = db.query(models.MovieShow).all()
    # Pydantic (with from_attributes=True) will automatically convert the list of ORM objects to the response schema
    return movies