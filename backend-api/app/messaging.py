import sys
sys.stdout.reconfigure(line_buffering=True)

import pika
import os
import json
from datetime import datetime

DELIVERY_MODE_PERSISTENT_VALUE = 2

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat() # Convert datetime object to ISO 8601 string
    raise TypeError ("Type %s not serializable" % type(obj))

# Load RabbitMQ connection details from environment variables
MQ_HOST = os.getenv("MQ_HOST", "rabbitmq_mq")
MQ_PORT = int(os.getenv("MQ_PORT", 5672))
MQ_USER = os.getenv("RABBITMQ_DEFAULT_USER", "rabbit_user")
MQ_PASS = os.getenv("RABBITMQ_DEFAULT_PASS", "rabbit_password")

# Define the names of the message queues
VIEW_EVENT_QUEUE = "view_event_queue"
EXTERNAL_SCORE_UPDATE_QUEUE = "external_score_update_queue"

def send_message(queue_name: str, message: dict):
    """
    Sends a JSON message to a specified RabbitMQ queue.
    """
    try:
        # 1. Establish connection to RabbitMQ broker
        credentials = pika.PlainCredentials(MQ_USER, MQ_PASS)
        parameters = pika.ConnectionParameters(
            host=MQ_HOST,
            port=MQ_PORT,
            credentials=credentials,
            # Heartbeat ensures connection is checked regularly
            heartbeat=600
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # 2. Declare the queue (creates it if it doesn't exist)
        channel.queue_declare(queue=queue_name, durable=True)

        # 3. Publish the message
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message, default=json_serial),
            properties=pika.BasicProperties(
                delivery_mode= DELIVERY_MODE_PERSISTENT_VALUE
            )
        )
        print(f" [x] Sent message to {queue_name}: {message}")
        connection.close()
        return True
    except pika.exceptions.AMQPConnectionError as e:
        print(f" [!] Failed to connect to RabbitMQ: {e}")
        # In a production app, we would retry or use a dead-letter queue
        return False
    except Exception as e:
        print(f" [!] An error occurred during messaging: {e}")
        return False