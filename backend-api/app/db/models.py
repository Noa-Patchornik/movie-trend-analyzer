# movie-trend-analyzer/backend-api/app/db/models.py

from sqlalchemy import Column, Integer, String, Float, DateTime, func, UniqueConstraint
from database import Base


# Define the ORM model for our movies/shows table
class MovieShow(Base):
    __tablename__ = "movies_and_shows"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Key for TMDB API (Must be unique)
    tmdb_id = Column(Integer, unique=True, nullable=False, index=True)

    # Movie/Show Details
    title = Column(String(255), nullable=False)
    release_date = Column(String(50), nullable=True)

    # Internal Metrics (Updated by Internal Worker)
    internal_views_count = Column(Integer, default=0, nullable=False)

    # External Metrics (Updated by External Worker)
    external_score = Column(Float, default=0.0, nullable=False)  # TMDB vote_average (0.0 to 10.0)

    # Combined Metric (The calculation)
    final_trend_score = Column(Float, default=0.0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    last_updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Ensure combination of columns is unique if needed, though tmdb_id is unique
    __table_args__ = (
        UniqueConstraint('tmdb_id', name='uq_tmdb_id'),
    )

    def __repr__(self):
        return f"<MovieShow(tmdb_id={self.tmdb_id}, title='{self.title}')>"