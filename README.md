# VYBE Restaurant & Food Discovery MVP

A full-stack restaurant and food search application with semantic search, MCP integration, and real-time observability.

**Tech Stack:**
- Backend: FastAPI (Python 3.11+) + Motor (async MongoDB)
- Frontend: React + Vite + Tailwind CSS
- Search: OpenAI embeddings (1536-dim) + MongoDB vector search + BAAI reranker
- Observability: Arize Phoenix + OpenTelemetry
- Package Manager: UV (fast, modern Python packaging)
- MCP Server: FastMCP (tool definitions for Claude integration)

## Architectural Pattern

### Service Layer (Composition)
- **RestaurantService**: Composes RestaurantRepository, HybridSearchService
- **FoodService**: Composes FoodRepository, HybridSearchService
- **HybridSearchService**: Generic orchestrator for semantic + manual search, reranking

### Repository Layer (Inheritance)
- Base: `BaseRepository` (async MongoDB patterns)
- Concrete: `MongoRestaurantRepository`, `MongoFoodRepository`

### API Layer (Endpoints)
- `/api/v1/restaurants/search` - Manual + filter-based search
- `/api/v1/restaurants/vector-search` - Semantic search
- `/api/v1/food/search` - Manual + filter-based search
- `/api/v1/food/vector-search` - Semantic search with allergen safety

### MCP Server Layer
- **vybesix-mcp**: FastMCP server with 4 tools for Claude integration
  - `search_restaurants_manual`
  - `search_restaurants_vector`
  - `search_food_manual`
  - `search_food_vector`

---

## Quick Start

### Prerequisites

**System Requirements:**
- Python 3.11+ (check with `python --version`)
- Node.js 18+ (check with `node --version`)
- UV package manager: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Docker + Docker Hub account (for deployment)
- MongoDB Atlas account (free tier available at mongodb.com)
- OpenAI API key (for embeddings: text-embedding-3-small)

**Environment Setup:**
```bash
# Create backend/.env with:
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
OPENAI_API_KEY=sk-...
DATABASE_NAME=vybe
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces  # optional for local dev
```

### Backend Setup (Using UV)

**Step 1: Install dependencies**
```bash
cd backend
uv sync
```

**Step 2: Run the FastAPI server**
```bash
uv run uvicorn app.main:app --reload
```

The server starts on `http://localhost:8000` with:
- ✅ FastAPI application
- ✅ MongoDB Atlas connection
- ✅ OpenAI embedding client initialization
- ✅ Arize Phoenix telemetry (if available)
- ✅ OpenTelemetry auto-instrumentation (FastAPI + OpenAI)
- ✅ Auto-loaded restaurants from database (lifespan event)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Server runs on `http://localhost:5173`

---

## What Gets Triggered When You Run the Backend

When you execute `uv run uvicorn app.main:app --reload`, these systems initialize:

1. **FastAPI Application**
   - RESTful API endpoints ready to accept requests
   - CORS middleware configured
   - Request/response validation via Pydantic models

2. **MongoDB Async Connection**
   - Establishes connection pool to MongoDB Atlas
   - Initializes repository layer for restaurants and food items
   - Seeds initial data (if first run)

3. **OpenAI Embedding Client**
   - Loads text-embedding-3-small model configuration
   - Ready to generate 1536-dimensional embeddings for queries and documents

4. **Arize Phoenix Observability**
   - Registers global OpenTelemetry tracer provider
   - Connects to Phoenix collector at `PHOENIX_COLLECTOR_ENDPOINT` (default: `http://localhost:6006/v1/traces`)
   - **Note:** In local dev, the embedded Phoenix server runs in background thread
   - **Note:** In production (Docker), Phoenix runs as separate service via docker-compose

5. **Auto-Instrumentation**
   - **FastAPI**: All HTTP requests/responses traced
   - **OpenAI**: All embedding calls traced (latency, token usage)
   - Spans sent to Phoenix for real-time visualization

6. **Lifespan Events**
   - On startup: Auto-loads all restaurants from database into memory
   - On shutdown: Graceful cleanup of database connections and telemetry

---

## Testing

### Prerequisites for Testing
- Backend running (or MongoDB connection available)
- OpenAI API key configured
- Test data seeded in MongoDB

### Running Tests

**Run all tests:**
```bash
cd backend
uv run pytest
```

**Run specific test file:**
```bash
uv run pytest test/test_food_hybrid_search_eval.py -v
```

**Run with coverage:**
```bash
uv run pytest --cov=app --cov-report=html
```

**Run a specific test:**
```bash
uv run pytest test/test_restaurant_service.py::test_search_with_geospatial_filter -v
```

### Test Files

| Test File | Purpose |
|-----------|---------|
| `test_restaurant_service.py` | RestaurantService with geospatial filtering and ranking |
| `test_food_hybrid_search_eval.py` | FoodHybridSearchService semantic search with allergen safety |
| `test_hybrid_search_service.py` | Generic HybridSearchService with embeddings and reranking |
| `test_vector_similarity.py` | Embedding quality and cosine similarity validation |
| `test_crewai_agents.py` | CrewAI agent orchestration tests |
| `conftest.py` | Pytest fixtures and MongoDB async setup |

---

## Observability Dashboard

### Local Development

Phoenix runs in the background when you start the backend:
```bash
cd backend
uv run uvicorn app.main:app --reload
# Phoenix UI automatically available at: http://localhost:6006
```

**Dashboard shows:**
- HTTP request traces (FastAPI endpoints)
- Embedding call traces (OpenAI API latency, token usage)
- Reranker latency (BAAI/bge-reranker-base)
- Full span timeline with parent-child relationships
- Query performance analysis

### Production Deployment (Docker)

Phoenix runs as a separate Docker service:
```bash
docker-compose up
# Phoenix available at: http://localhost:6006
```

Configuration:
- Container: `arizephoenix/phoenix:latest`
- Port: `6006:6006`
- Backend connects via: `PHOENIX_COLLECTOR_ENDPOINT=http://phoenix-observability:6006/v1/traces`

---

## API Documentation

Once the backend is running, visit:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Key Endpoints

**Restaurant Search:**
- `POST /api/v1/restaurants/search` - Manual filtering (cuisine, price, amenities)
- `POST /api/v1/restaurants/vector-search` - Semantic search ("quiet place for work")

**Food Search:**
- `POST /api/v1/food/search` - Manual filtering (dietary, allergens, prep time)
- `POST /api/v1/food/vector-search` - Semantic search ("quick vegan protein bowl")

**Request Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/restaurants/vector-search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "quiet cafe for working",
    "num_candidates": 5
  }'
```

## Project Structure

```
.
├── backend/                              # FastAPI backend service
│   ├── app/
│   │   ├── api/v1/                      # API endpoints (restaurants, food)
│   │   ├── services/                    # Business logic (RestaurantService, FoodService)
│   │   ├── repositories/                # MongoDB data layer
│   │   ├── pipeline_models/             # Rerankers, embedding adapters
│   │   ├── model/                       # Pydantic schemas
│   │   ├── observability/               # Phoenix + OpenTelemetry setup
│   │   └── main.py                      # FastAPI application
│   ├── test/                            # Pytest integration & unit tests
│   ├── scripts/                         # Database seeding scripts
│   ├── pyproject.toml                   # UV dependencies (replaces Pipfile)
│   ├── uv.lock                          # Lock file for reproducible installs
│   ├── requirements_dev.txt             # Dev dependencies
│   ├── Dockerfile                       # Container image for backend
│   └── .env.example                     # Environment template
├── frontend/                             # React + Vite frontend
│   ├── src/
│   │   ├── components/                  # React components
│   │   ├── hooks/                       # Custom React hooks
│   │   └── App.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile                       # Container image for frontend
├── vybesix-mcp/                         # MCP server for Claude integration
│   ├── src/vybesix_mcp/
│   │   ├── server.py                    # FastMCP server with 4 tools
│   │   └── __init__.py
│   ├── pyproject.toml
│   └── Dockerfile
├── agents/                               # AI developer's agent code (separate repo)
│   └── (CrewAI, LangGraph, or similar)
├── docker-compose.yml                   # Orchestrates all services
└── Deployment.md                        # Deployment guide
```

## Development

### Backend Stack
- **Framework:** FastAPI + Uvicorn
- **Database:** Motor (async MongoDB driver)
- **Search:** OpenAI embeddings + MongoDB vector search
- **Reranking:** BAAI/bge-reranker-base
- **Testing:** Pytest + async fixtures
- **Observability:** Arize Phoenix + OpenTelemetry
- **Package Manager:** UV (100x faster than pip)

### Frontend Stack
- **Framework:** React 18 + Vite (HMR enabled)
- **Styling:** Tailwind CSS
- **HTTP Client:** Fetch API
- **MCP Integration:** Claude MCP client (for agent queries)

### Data Flow

```
User Query
    ↓
Frontend (React)
    ↓
MCP Client → MCP Server (vybesix-mcp)
    ↓
FastAPI Backend API
    ↓
Repository Layer → MongoDB Vector Search
    ↓
Reranker (BAAI/bge-reranker-base)
    ↓
Results → Phoenix Observability Dashboard
    ↓
Frontend Display
```

---

## Database Seeding

### Restaurant Data
```bash
cd backend
uv run python scripts/seed_restaurants.py
```

### Food Data
```bash
cd backend
uv run python scripts/seed_food.py
```

Both scripts:
1. Transform raw JSON into MongoDB documents
2. Generate OpenAI embeddings (1536-dim)
3. Create MongoDB vector search index
4. Load into MongoDB Atlas

---

## Deployment

See **Deployment.md** for:
- Building Docker images (`anmolgg/vybesix-backend:v1`, `anmolgg/vybesix-mcp-server:v1`)
- Creating shared workspace structure
- Running multi-container environment with docker-compose
- Connecting Phoenix observability service

---

## Troubleshooting

**Backend won't start:**
```bash
# Check dependencies installed
uv sync

# Check MongoDB connection
python -c "import motor; print('Motor OK')"

# Check OpenAI key
echo $OPENAI_API_KEY
```

**Tests failing:**
```bash
# Ensure MongoDB has test data
cd backend && uv run python scripts/seed_restaurants.py

# Run with verbose output
uv run pytest -vv --tb=short
```

**Phoenix not showing spans:**
```bash
# Check endpoint in backend/.env
export PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6006/v1/traces

# Restart backend
uv run uvicorn app.main:app --reload
```