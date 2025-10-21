# movie-trend-analyzer/internal-worker/worker_app/internal_processor.py

import os
import sys
sys.stdout.reconfigure(line_buffering=True)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pika
import json
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import MovieShow
from db.database import SQLALCHEMY_DATABASE_URL # Import DB URL configuratio

# --- 1. Database Setup ---
# The Worker needs its own separate connection to the DB
print("INFO: Setting up database connection for Internal Worker...")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    """Returns a new DB session for transaction processing."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


# --- 2. RabbitMQ Setup ---
MQ_HOST = os.getenv("MQ_HOST", "rabbitmq_mq")
MQ_PORT = int(os.getenv("MQ_PORT", 5672))
MQ_USER = os.getenv("RABBITMQ_DEFAULT_USER", "rabbit_user")
MQ_PASS = os.getenv("RABBITMQ_DEFAULT_PASS", "rabbit_password")
QUEUE_NAME = "view_event_queue"


# --- 3. Core Logic ---
def update_view_count(db_session, tmdb_id: int):
    """
    Finds a movie by tmdb_id and increments its internal_views_count.
    """
    # 1. Find the movie record
    movie_record = db_session.query(MovieShow).filter(MovieShow.tmdb_id == tmdb_id).first()

    if movie_record:
        # 2. Increment the counter
        movie_record.internal_views_count += 1
        movie_record.last_updated_at = func.now()  # Manually update timestamp (optional if using onupdate)

        # 3. Commit the changes to the database
        db_session.commit()
        print(f"SUCCESS: Incremented views for TMDB ID {tmdb_id}. New count: {movie_record.internal_views_count}")
    else:
        print(f"ERROR: TMDB ID {tmdb_id} not found in DB. Skipping.")


# --- 4. RabbitMQ Consumer Callback ---
def callback(ch, method, properties, body):
    """
    This function is called every time a message is received from the queue.
    """
    try:
        message_data = json.loads(body)
        tmdb_id = message_data.get('tmdb_id')
        event_type = message_data.get('event_type')

        print(f" [x] Received message: {event_type} for TMDB ID: {tmdb_id}")

        if event_type == "VIEW" and tmdb_id:
            # Get a fresh database session for this transaction
            db_session = get_db_session()
            update_view_count(db_session, tmdb_id)
        else:
            print(f"WARNING: Unknown event type or missing TMDB ID: {message_data}")

    except Exception as e:
        print(f"CRITICAL ERROR processing message: {e}")
    finally:
        # Acknowledge the message only after successful processing and DB commit
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(" [x] Message acknowledged.")


# --- 5. Main Consumer Loop ---
def start_consuming():
    """
    Establishes connection to RabbitMQ and starts listening for messages.
    """
    print("INFO: Internal Worker starting...", flush = True)

    # Use a loop to retry connection in case MQ is not ready yet
    for attempt in range(10):
        try:
            credentials = pika.PlainCredentials(MQ_USER, MQ_PASS)
            parameters = pika.ConnectionParameters(
                host=MQ_HOST,
                port=MQ_PORT,
                credentials=credentials,
                retry_delay=5,
                heartbeat=600
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()

            # Make sure the queue exists before consuming from it
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            print(f' [*] Waiting for messages on {QUEUE_NAME}. To exit press CTRL+C', flush= True)

            # Set up the consumer
            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=callback,
                auto_ack=False
            )

            try:
                channel.start_consuming()
            except Exception as e:
                print(f"[!] Worker crashed with error: {e}", flush=True)

            break

        except pika.exceptions.AMQPConnectionError:
            print(f"WARNING: RabbitMQ not ready. Retrying in 5 seconds (Attempt {attempt + 1}/10)...", flush=True)
            time.sleep(5)
        except Exception as e:
            print(f"CRITICAL ERROR in Internal Worker: {e}", flush=True)
            break


if __name__ == '__main__':
    # We'll need to update the Dockerfile to make the backend-api code accessible
    # to the workers, or copy the necessary DB files.
    # For now, we assume a linked project structure or copying of DB files.
    from sqlalchemy import func

    print("Worker started and waiting for messages...", flush = True)

    start_consuming()