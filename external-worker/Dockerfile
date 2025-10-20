# Dockerfile: internal-worker / external-worker (Common structure)
FROM python:3.10-slim
WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# 1. Copy the necessary DB files from backend-api for shared models
# This links the DB knowledge without linking the entire API server
COPY ../backend-api/app/db /app/db/

# 2. Copy worker requirements and install dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the worker application code
COPY ./worker_app /app/worker_app

# Set the command to run the main worker script
CMD ["python", "worker_app/external_scorer.py"]