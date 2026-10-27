# VYBE Restaurant & Food Discovery

Restaurant and food search for Claude. Ask in plain language and Claude calls the search tools, which filter on dietary rules, allergens, price, amenities and location, then rank by meaning.

## Example Result

![Vector search result](TestImage/vector_search_result.png)

## Table of Contents

- [Components](#components)
- [Dataset](#dataset)
- [System Design](#system-design)
- [Quick Start](#quick-start)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Download the repo](#2-download-the-repo)
  - [3. Configure environment variables](#3-configure-environment-variables)
  - [4. Set up the database](#4-set-up-the-database)
  - [5. Start the FastAPI server](#5-start-the-fastapi-server)
  - [6. Connect Claude to the MCP server](#6-connect-claude-to-the-mcp-server)
  - [7. Frontend (optional)](#7-frontend-optional)
- [Testing](#testing)
- [Observability Dashboard](#observability-dashboard)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Backend Stack](#backend-stack)
- [Troubleshooting](#troubleshooting)

## Components

| Component | Role |
|---|---|
| **MCP host (Claude)** | Reads the tool list, chooses a tool, and turns the answer into text |
| **MCP server (FastMCP)** | `vybesix-mcp`: exposes four tools and forwards each call to the FastAPI backend |
| **FastAPI backend** | `backend/`: validates requests, runs search services, and returns JSON |
| **MongoDB Atlas** | Stores restaurants, food and users, runs geospatial and vector search |
| **OpenAI** | Creates 1536-dim embeddings (`text-embedding-3-small`) for documents and queries |

## Dataset

### Restaurant (`restaurants`)

| Field | Type | Notes |
|---|---|---|
| `restaurant_id` | string | Unique ID, e.g. `restaurant_3` |
| `name`, `slug`, `description` | string | Display and search text |
| `location` | GeoJSON Point | `{"type": "Point", "coordinates": [long, lat]}` |
| `cuisine`, `dietary`, `meal_types` | string[] | e.g. `dietary: ["vegan", "vegetarian"]` |
| `has_parking`, `has_live_music` | bool | Native booleans |
| `price_max` | number | Maximum price in dollars |
| `rating`, `max_capacity` | number | |
| `service_hours` | object | `{"Monday": {"open": 720, "close": 1320}}`, minutes from midnight |
| `ai_metadata` | object | Mood, occasion and taste tags |
| `vector_embeddings` | float[1536] | Search vector |

### Food (`food`)

| Field | Type | Notes |
|---|---|---|
| `food_id` | string | e.g. `food_restaurant_1_1` |
| `restaurant_id` | string | Links to a restaurant |
| `name`, `description` | string | |
| `category` | string | `appetizer`, `main_course`, `dessert`, `breakfast`, `beverage` |
| `cuisine`, `dietary`, `meal_types` | string[] | |
| `allergens` | string[] | e.g. `peanuts`, `soy`, `dairy`. Excluded when requested |
| `ingredients`, `preparation_method` | string[] | |
| `price` | number | Dish price in dollars |
| `spice_level` | int | 0–5 |
| `calories`, `prep_time_minutes` | int | |
| `vegan_friendly`, `vegetarian_friendly`, `gluten_free` | bool | Native booleans |
| `vector_embeddings` | float[1536] | Search vector |

## System Design

### API layer and MCP tools

| FastMCP tool (`vybesix-mcp`) | FastAPI endpoint (`backend`) |
|---|---|
| `search_restaurants_manual` | `POST /api/v1/restaurants/search` |
| `search_restaurants_vector` | `POST /api/v1/restaurants/vector-search` |
| `search_food_manual` | `POST /api/v1/food/search` |
| `search_food_vector` | `POST /api/v1/food/vector-search` |

### Backend layers

- **API** (`app/api/v1/`): validates requests with Pydantic and calls a service.
- **Service** (`app/services/`): applies preference injection and orchestrates search.
- **Repository** (`app/repositories/`): builds MongoDB aggregation pipelines.
- **Adapters** (`app/pipeline_models/`): embedding and reranking models.

### Data flow

1. **Intent:** the user asks in natural language. Claude reads the tool list and chooses a tool with arguments.
2. **Search:** the MCP server calls the matching FastAPI endpoint. The repository runs a MongoDB query with safety filters first: dietary, allergens, price and amenities. Vector search only considers the restaurant IDs it is given.
3. **Ranking:** for vector search, a cross-encoder reranker (`ms-marco-MiniLM-L-6-v2`) scores each candidate against the query. Results below -2.0 are dropped.
4. **Return:** the API returns JSON to the MCP server, which returns it to Claude.

## Quick Start

### 1. Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- A MongoDB Atlas cluster (free tier works)
- An OpenAI API key
- Claude Desktop or Claude Code

### 2. Download the repo

```bash
git clone <your-repo-url> radiocalico
cd radiocalico
```

### 3. Configure environment variables

Create `backend/.env`:

```bash
cp backend/.env.example backend/.env
```

| Variable | Required | Example |
|---|---|---|
| `MONGODB_URL` | Yes | `mongodb+srv://user:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority` |
| `DATABASE_NAME` | Yes | `vybe` |
| `OPENAI_API_KEY` | Yes | `sk-...` |
| `PHOENIX_COLLECTOR_ENDPOINT` | No | `http://localhost:6006/v1/traces` |

The MCP server reads `API_BASE_URL` (default `http://localhost:8000`). Set it only if the backend runs elsewhere.

### 4. Set up the database

Run the seed scripts in this order from the `backend` folder. They create the data, the embeddings and the vector search indexes.

```bash
cd backend
uv sync
uv run python scripts/seed_database.py
uv run python scripts/seed_food.py
```

- `seed_database.py` replaces all restaurants and users with `test/restaurants.json` and `test/users.json`.
- `seed_food.py` inserts food items without clearing the collection. Run it on an empty `food` collection, or it will create duplicates.
- Atlas builds each vector index in about a minute. Wait until both show `READY` in the Atlas UI (Atlas Search → Indexes) before searching.

### 5. Start the FastAPI server

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Check that it's running: open `http://localhost:8000/docs`.

### 6. Connect Claude to the MCP server

Install the MCP server's dependencies first:

```bash
cd vybesix-mcp
uv sync
```

Find the absolute path to `uv`, then replace the placeholders below:

```bash
which uv
```

**Claude Desktop:** edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vybesix": {
      "command": "/absolute/path/to/uv",
      "args": ["run", "--directory", "/absolute/path/to/radiocalico/vybesix-mcp", "python", "-m", "vybesix_mcp"]
    }
  }
}
```

**Claude Code:** run this once from the repo folder:

```bash
claude mcp add vybesix -- /absolute/path/to/uv run --directory /absolute/path/to/radiocalico/vybesix-mcp python -m vybesix_mcp
```

Restart Claude Desktop, or start a new Claude Code session. In Claude Code, run `/mcp` to confirm `vybesix` is connected with four tools.

The backend must be running (step 5) for the tools to return results.

### 7. Frontend (optional)

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

---

## Testing

Tests need the backend's `.env` file, a seeded database and an OpenAI key.

```bash
cd backend
uv run pytest
```

Run one file:

```bash
uv run pytest test/test_restaurant_service.py -v
```

`test_restaurant_eval.py` and `test_food_hybrid_search_eval.py` call the OpenAI API, so they cost money to run. Restaurant eval output is written to `test/search_experiments.log`.

### Test files

| Test File | Purpose |
|-----------|---------|
| `test_restaurant_service.py` | RestaurantService with geospatial filtering, dietary and preference injection |
| `test_restaurant_eval.py` | RestaurantHybridSearchService semantic search with allergen safety |
| `test_food_hybrid_search_eval.py` | FoodHybridSearchService semantic search with allergen safety |
| `test_vector_similarity.py` | Embedding quality and cosine similarity validation |
| `conftest.py` | Pytest fixtures and MongoDB async setup |

---

## Observability Dashboard

Phoenix shows HTTP request traces, OpenAI embedding calls, reranker latency and span timelines. Choose one option:

**Option A: Run Phoenix as a separate service (Recommended)**
```bash
# Terminal 1: Install and run Phoenix
uv pip install arize-phoenix
phoenix
# Phoenix available at: http://localhost:6006

# Terminal 2: Start backend (connects to Phoenix automatically)
cd backend
uv run uvicorn app.main:app --reload
```

**Option B: Run Phoenix as a Docker container**
```bash
# Terminal 1: Start Phoenix container
docker run -d -p 6006:6006 arizephoenix/phoenix:latest
# Phoenix available at: http://localhost:6006

# Terminal 2: Start backend
cd backend
uv run uvicorn app.main:app --reload
```

**Option C: Embedded Phoenix (Simpler, single terminal)**
```bash
# Edit backend/app/observability/setup.py and uncomment line 27:
# Change: # px.launch_app()
# To: px.launch_app()

# Then start backend (Phoenix launches automatically)
cd backend
uv run uvicorn app.main:app --reload
# Phoenix available at: http://localhost:6006
```

---

## API Documentation

Once the backend is running:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Key Endpoints

**Restaurant Search:**
- `POST /api/v1/restaurants/search`: manual filtering (dietary, price, amenities, cuisine, location)
- `POST /api/v1/restaurants/vector-search`: semantic search within a list of restaurant IDs

**Food Search:**
- `POST /api/v1/food/search`: manual filtering (dietary, allergens, category, price, prep time)
- `POST /api/v1/food/vector-search`: semantic search within a list of restaurant IDs

Restaurant search returns only restaurants open at the time of the request. Add `?bypass_hours=true` to include closed restaurants.

**Request example:**
```bash
curl -X POST "http://localhost:8000/api/v1/restaurants/vector-search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "quiet cafe for working",
    "restaurant_ids": ["restaurant_9", "restaurant_17", "restaurant_19"],
    "limit": 5
  }'
```

---

## Project Structure

```
.
├── backend/                              # FastAPI backend service
│   ├── app/
│   │   ├── api/v1/                       # API endpoints (restaurants, food)
│   │   ├── services/                     # Business logic (RestaurantService, FoodService)
│   │   ├── repositories/                 # MongoDB data layer
│   │   ├── pipeline_models/              # Rerankers, embedding adapters
│   │   ├── model/                        # Pydantic schemas
│   │   ├── observability/                # Phoenix + OpenTelemetry setup
│   │   └── main.py                       # FastAPI application
│   ├── test/                             # Pytest integration & eval tests
│   ├── scripts/                          # Database seeding and check scripts
│   ├── pyproject.toml                    # UV dependencies
│   ├── uv.lock                           # Lock file for reproducible installs
│   └── .env.example                      # Environment template
├── vybesix-mcp/                          # FastMCP server for Claude
│   ├── src/vybesix_mcp/
│   │   ├── server.py                     # FastMCP server with 4 tools
│   │   └── __main__.py                   # Entry point (python -m vybesix_mcp)
│   └── pyproject.toml
└── frontend/                             # React + Vite frontend (optional)
    ├── src/
    └── package.json
```

## Backend Stack

- **Framework:** FastAPI + Uvicorn
- **Database:** PyMongo AsyncMongoClient (async MongoDB driver) on MongoDB Atlas
- **Search:** OpenAI embeddings (`text-embedding-3-small`) + MongoDB Atlas vector search
- **Reranking:** `ms-marco-MiniLM-L-6-v2` cross-encoder
- **Testing:** Pytest + async fixtures
- **Observability:** Arize Phoenix + OpenTelemetry
- **Package manager:** UV

## Troubleshooting

**Backend won't start:**
```bash
cd backend
uv sync
uv run python scripts/check_mongo_connection.py
echo $OPENAI_API_KEY
```

**`dns query name does not exist` or connection errors:** the `MONGODB_URL` hostname is wrong or the cluster is paused or deleted. Copy the current connection string from Atlas (Connect → Drivers) into `backend/.env`.

**Search returns no results:** check that the seed scripts ran and that both vector indexes show `READY`. Restaurant search also excludes closed restaurants unless you pass `bypass_hours=true`.

**Claude shows `vybesix` as disconnected:** run `/mcp` (Claude Code) to see the error. Check that the path in the config points to `vybesix-mcp` and that `uv sync` ran in that folder. Make sure the backend is running on port 8000.

**Tests failing:**
```bash
cd backend
uv run pytest -vv --tb=short
```

**Phoenix not showing spans:**
```bash
# Check endpoint in backend/.env
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces

# Restart backend
uv run uvicorn app.main:app --reload
```