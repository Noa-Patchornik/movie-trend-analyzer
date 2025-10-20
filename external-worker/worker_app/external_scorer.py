# movie-trend-analyzer/external-worker/worker_app/external_scorer.py

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pika
import json
import time
import requests  # Used for making HTTP calls to TMDB
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from db.models import MovieShow  # Relying on Dockerfile to copy this file
from db.database import SQLALCHEMY_DATABASE_URL  # Relying on Dockerfile to copy this file

# --- 1. Configuration and Setup ---
print("INFO: Setting up database connection for External Worker...")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

MQ_HOST = os.getenv("MQ_HOST", "rabbitmq_mq")
MQ_USER = os.getenv("RABBITMQ_DEFAULT_USER")
MQ_PASS = os.getenv("RABBITMQ_DEFAULT_PASS")
MQ_PORT = int(os.getenv("MQ_PORT", 5672))
QUEUE_NAME = "external_score_update_queue"

# TMDB API Key loaded from environment
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3/movie/"


# --- 2. External API Logic ---
def fetch_tmdb_data(tmdb_id: int):
    """Fetches movie title and vote average from TMDB."""
    if not TMDB_API_KEY:
        print("CRITICAL: TMDB_API_KEY is missing!")
        return None

    # Construct the full URL for TMDB API call
    url = f"{TMDB_BASE_URL}{tmdb_id}?api_key={TMDB_API_KEY}"

    try:
        response = requests.get(url, timeout=10)  # Set a timeout for external calls
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()

        # Check if TMDB returned a valid response
        if 'title' in data and 'vote_average' in data:
            return {
                'title': data['title'],
                'external_score': data['vote_average'],
                'release_date': data.get('release_date', None)
            }
        else:
            print(f"ERROR: TMDB response missing title or vote_average for ID {tmdb_id}.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to fetch data from TMDB for ID {tmdb_id}. Error: {e}")
        return None


# --- 3. Core Calculation Logic ---
def update_external_score_and_calculate_trend(db_session, tmdb_id: int):
    """
    Fetches external data, calculates the final trend score, and updates the DB.
    """
    # 1. Fetch TMDB data
    tmdb_data = fetch_tmdb_data(tmdb_id)
    if not tmdb_data:
        # If external data fetch failed, we stop here and acknowledge the message.
        return

    # 2. Find the movie record in our DB
    movie_record = db_session.query(MovieShow).filter(MovieShow.tmdb_id == tmdb_id).first()

    if movie_record:
        # 3. Update Title and External Score
        movie_record.title = tmdb_data['title']  # Update placeholder title
        movie_record.external_score = tmdb_data['external_score']

        # 4. Calculate Final Trend Score (The logic demonstration)
        # We'll use a simple weighted average: 70% TMDB Score, 30% Internal Views (normalized)

        # Normalize internal views
        # This normalization is illustrative. Real systems use much more complex logic.
        MAX_VIEWS_FOR_FULL_SCORE = 100

        normalized_internal_score = min(movie_record.internal_views_count / MAX_VIEWS_FOR_FULL_SCORE, 1.0) * 10.0

        # Simple Weighted Average
        final_score = (
                (movie_record.external_score * 0.7) +
                (normalized_internal_score * 0.3)
        )

        movie_record.final_trend_score = round(final_score, 1)

        # 5. Commit changes
        movie_record.last_updated_at = func.now()
        db_session.commit()
        print(
            f"SUCCESS: Calculated Trend Score for '{movie_record.title}' ({tmdb_id}). Score: {movie_record.final_trend_score}")
    else:
        print(f"ERROR: TMDB ID {tmdb_id} not found in DB. Skipping.")


# --- 4. RabbitMQ Consumer Callback
def callback(ch, method, properties, body):
    try:
        message_data = json.loads(body)
        tmdb_id = message_data.get('tmdb_id')
        event_type = message_data.get('event_type')

        print(f" [x] Received external update event: {event_type} for TMDB ID: {tmdb_id}")

        if tmdb_id:
            db_session = SessionLocal()  # Open new session
            update_external_score_and_calculate_trend(db_session, tmdb_id)
        else:
            print(f"WARNING: Message missing TMDB ID: {message_data}")

    except Exception as e:
        print(f"CRITICAL ERROR processing message: {e}")
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        db_session.close()  # Ensure the session is closed


# --- 5. Main Consumer Loop ---
def start_consuming():
    """
    Establishes connection to RabbitMQ, starts listening for messages,
    and implements a retry mechanism.
    """
    print("INFO: Worker starting...")

    # Connection parameters from environment
    credentials = pika.PlainCredentials(MQ_USER, MQ_PASS)
    parameters = pika.ConnectionParameters(
        host=MQ_HOST,
        port=MQ_PORT,
        credentials=credentials,
        heartbeat=600  # Connection health check
    )

    # Retry mechanism for connecting to RabbitMQ
    MAX_RETRIES = 10

    for attempt in range(MAX_RETRIES):
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            # Declare the queue (creates it if it doesn't exist)
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            print(f' [*] Waiting for messages on {QUEUE_NAME}. To exit press CTRL+C')

            # Start consuming messages
            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=callback,
                auto_ack=False
            )

            channel.start_consuming()

            break

        except pika.exceptions.AMQPConnectionError:
            if attempt < MAX_RETRIES - 1:
                print(f"WARNING: RabbitMQ not ready. Retrying in 5 seconds (Attempt {attempt + 1}/{MAX_RETRIES})...")
                time.sleep(5)
            else:
                print("CRITICAL: Failed to connect to RabbitMQ after multiple retries. Exiting.")
                raise  # Raise the exception if retries failed

        except KeyboardInterrupt:
            print(" [*] Worker shutting down...")
            break

        except Exception as e:
            print(f"CRITICAL ERROR in Worker: {e}")
            break


# Ensure the main part calls the function
if __name__ == '__main__':
    # Import func for the standalone run
    from sqlalchemy import func

    start_consuming()