# Dockerfile: backend-api
# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install dependencies needed for psycopg2 (PostgreSQL adapter)
# This step is crucial for connecting Python to Postgres
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install Python dependencies
# We assume a requirements.txt file will be created next
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY ./app /app/app

# Command to run the application using Uvicorn (FastAPI server)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]