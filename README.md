# 🎬 Movie Trend Analyzer - Event-Driven Microservices MVP

## Project Overview

**Movie Trend Analyzer** is a Minimum Viable Product (MVP) backend system designed to calculate a real-time Final Trend Score for movies and TV shows.  
It demonstrates a robust, production-ready architecture by integrating multiple microservices that communicate asynchronously.

This project was developed as a learning exercise in Microservices Architecture, focusing on:  
- Asynchronous Communication using RabbitMQ (Message Queues)  
- Containerization with Docker Compose  

---

## Key Technologies

| Category           | Technology                          | Purpose                                                                 |
|-------------------|------------------------------------|-------------------------------------------------------------------------|
| Backend API        | Python 3.10, FastAPI                | High-performance API Gateway that handles user requests                 |
| Messaging/Queue    | RabbitMQ, Pika                      | Manages asynchronous events (Views, External Updates)                   |
| Database/ORM       | PostgreSQL (Docker), SQLAlchemy     | Persistent storage for movie data and calculated scores                 |
| External Data      | TMDB API (The Movie Database)       | Source for fetching external vote averages and movie details            |
| Containerization   | Docker Compose                      | Orchestrates all 6 services (API, 2x Workers, DB, MQ, Frontend)        |
| Frontend UI        | React (Vite/JS), NGINX Proxy       | Simple UI for visualization and triggering events                       |
| Development        | Vibe Coding                          | Rapid prototyping and implementation of core architectural concepts    |

---

## Architecture and Data Flow

The system is split into multiple distinct services, demonstrating a decoupled, Event-Driven Architecture (EDA):

1. **FastAPI (API Gateway)**:  
   - Receives user actions (`POST /view`, `POST /register`)  
   - Immediately saves basic data to the DB and publishes a JSON Event to RabbitMQ (`Status: 202 Accepted`)  

2. **RabbitMQ**:  
   - Holds events in dedicated queues (`view_event_queue`, `external_score_update_queue`)  

3. **Internal Worker**:  
   - Consumes VIEW events  
   - Increments `internal_views_count` in PostgreSQL  

4. **External Worker**:  
   - Consumes UPDATE events  
   - Calls TMDB API for external scores  
   - Calculates the Final Trend Score (weighted average)  
   - Updates PostgreSQL, deletes entries if TMDB returns 404  

5. **PostgreSQL**:  
   - Single source of truth for all data, updated asynchronously  

6. **Frontend/NGINX**:  
   - Fetches final, calculated scores from FastAPI  
   - Displays results on the dashboard  

---

## 💻 Project Setup and Installation

### Prerequisites
- Docker Desktop (or Docker Engine)  
- Git  
- TMDB API Key (v3) saved in `.env` file  

### Step 1: Clone the Repository

```bash
git clone [(https://github.com/Noa-Patchornik/movie-trend-analyzer)] movie-trend-analyzer
cd movie-trend-analyzer
```

### Step 2: Create the Environment File

Create a file named .env in the root directory:

```bash
# .env

# --- POSTGRES CONFIG ---
POSTGRES_USER=postgres_user
POSTGRES_PASSWORD=strong_password
POSTGRES_DB=trend_db
DB_HOST=postgres_db 

# --- RABBITMQ CONFIG ---
RABBITMQ_DEFAULT_USER=rabbit_user
RABBITMQ_DEFAULT_PASS=rabbit_password
MQ_HOST=rabbitmq_mq

# --- EXTERNAL API KEY ---
TMDB_API_KEY=YOUR_ACTUAL_TMDB_API_KEY_HERE

# --- APP PORT ---
FASTAPI_PORT=8000
```

### Step 3: Run with Docker Compose

```bash
# -v: Clears old database data (recommended for fresh start)
# --build: Ensures all latest code changes are compiled into the images
docker-compose up --build -d
```

### Step 4: Verification

Check that all containers are running:

| Service           | Host Port | Purpose                                  | Status Check                                                                 |
|------------------|-----------|------------------------------------------|------------------------------------------------------------------------------|
| FastAPI API       | 8000      | Gateway & Data Read                      | [Swagger UI](http://localhost:8000/docs)                                     |
| Frontend UI       | 3000      | Dashboard                                | [Open Dashboard](http://localhost:3000)                                      |
| RabbitMQ Admin    | 15672     | Check Queues                             | [RabbitMQ Management](http://localhost:15672)                                |
| Internal Worker   | -         | Processes VIEW events, updates DB        | Check logs: `docker logs internal-worker`                                     |
| External Worker   | -         | Processes EXTERNAL_UPDATE events, fetches TMDB, calculates score | Check logs: `docker logs external-worker`                                     |
| PostgreSQL DB     | 5432      | Database                                 | Connect with DB client to verify tables                                       |


## 🧪 Testing the Full E2E Flow

Follow these steps to test the complete end-to-end workflow:

### 1. Register a Movie
- **Endpoint:** `POST /api/movies/register`  
- **Description:** Registers a movie in the system using a valid TMDB ID (e.g., `27205`).  
- **Purpose:**  
  - Verifies that FastAPI and PostgreSQL are working correctly.  
  - Ensures the External Worker receives the `INITIAL_EXTERNAL_UPDATE` event.  
- **Verification:** Check `external_worker` logs for successful TMDB fetch, title update, and final score calculation.  

### 2. Add a View
- **Endpoint:** `POST /api/movies/view`  
- **Description:** Adds a view for the same TMDB movie ID.  
- **Purpose:** Confirms that the Internal Worker processes view events correctly.  
- **Verification:** Check `internal_worker` logs for successful view increment.  

### 3. Verify Dashboard
- **URL:** [http://localhost:3000](http://localhost:3000)  
- **Description:** View the dashboard to ensure all data is displayed correctly.  
- **Expected Result:** The table should show the movie with updated view counts and the calculated Final Trend Score.


## 📂 Project Structure

```bash
movie-trend-analyzer/
├── backend-api/             # FastAPI Service (Port 8000)
│   ├── app/                 # Python source code
│   │   ├── api/             # Routers (movies.py)
│   │   ├── db/              # SQLAlchemy Models (models.py, database.py, __init__.py)
│   │   └── main.py          # App initialization and CORS setup
│   ├── requirements.txt     # FastAPI, SQLAlchemy, pika, uvicorn
│   └── Dockerfile           
├── internal-worker/         # Worker 1: Handles VIEW events
│   ├── worker_app/
│   │   └── internal_processor.py # Consumes MQ, updates views
│   └── Dockerfile
├── external-worker/         # Worker 2: Handles EXTERNAL_UPDATE events
│   ├── worker_app/
│   │   └── external_scorer.py    # Consumes MQ, fetches TMDB, calculates score, updates DB
│   └── Dockerfile
├── frontend/                # React/Vite UI (Port 3000)
│   ├── src/                 # React source (App.jsx)
│   ├── nginx.conf           # Reverse Proxy configuration (routes /api to FastAPI)
│   ├── package.json         
│   └── Dockerfile           # Node 20+ for Vite build, Nginx for serving
├── docker-compose.yml       # Orchestrates all 6 services
├── .env                     # Configuration file
└── README.md                # This file
```
