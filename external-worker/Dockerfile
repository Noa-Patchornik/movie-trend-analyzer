# Dockerfile: external-worker
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./worker_app /app/worker_app

# The command will be defined later in the code development phase
CMD ["python", "worker_app/external_scorer.py"]