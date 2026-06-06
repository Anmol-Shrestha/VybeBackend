# VYBE System Architecture Overview

## Team Structure

Three developers working on separate, integrated components:

| Role | Responsibility | Technology | Status |
|------|---|---|---|
| **Backend Developer** (You) | Database, APIs, MCP Server | FastAPI, PyMongo, FastMCP | ✅ Complete |
| **Frontend Developer** | UI, MCP Client, Tool Discovery | React, Vite, @modelcontextprotocol/sdk | 🔄 In Progress |
| **AI Developer** | Agent Orchestration, Claude Integration | CrewAI/LangGraph, Claude 3.5 Sonnet | 🔄 In Progress |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            USER INTERACTION LAYER                            │
│                                                                              │
│  User Types Query → React Frontend (http://localhost:5173)                  │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────────────┐
│                         FRONTEND (MCP CLIENT)                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ React App (SearchChat Component)                                    │   │
│  │ • Captures user query                                               │   │
│  │ • Has MCP Client connection                                         │   │
│  │ • Discovers tools from vybesix-mcp                                  │   │
│  └────────────────────┬────────────────────────────────────────────────┘   │
│                       │                                                     │
│                       │ connects via stdio                                  │
│                       │ MCP Protocol                                        │
└───────────────────────┼─────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────────────────┐
│                    VYBESIX-MCP (TOOL PROVIDER)                              │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ FastMCP Server (vybesix-mcp/src/vybesix_mcp/server.py)              │  │
│  │                                                                       │  │
│  │ • Exposes 4 tools via MCP protocol:                                 │  │
│  │   ✅ search_restaurants_manual                                       │  │
│  │   ✅ search_restaurants_vector                                       │  │
│  │   ✅ search_food_manual                                              │  │
│  │   ✅ search_food_vector                                              │  │
│  │                                                                       │  │
│  │ • Tools call backend APIs (httpx client)                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                       │                                                     │
│                       │ each tool calls                                     │
│                       │ backend API endpoint                                │
└───────────────────────┼─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┬───────────────┐
        │               │               │               │
        ▼               ▼               ▼               ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ /api/v1/ │    │ /api/v1/ │    │ /api/v1/ │    │ /api/v1/ │
│restaurants/   │restaurants/   │   food/  │    │   food/  │
│  search      │vector-search  │  search  │    │vector... │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
        │               │               │               │
        └───────────────┼───────────────┴───────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────────────────┐
│                    BACKEND API LAYER                                         │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ FastAPI Application (backend/app/main.py)                           │  │
│  │                                                                       │  │
│  │ • REST Endpoints:                                                    │  │
│  │   POST /api/v1/restaurants/search      (manual filtering)           │  │
│  │   POST /api/v1/restaurants/vector-search (semantic search)          │  │
│  │   POST /api/v1/food/search             (manual filtering)           │  │
│  │   POST /api/v1/food/vector-search      (semantic search)            │  │
│  │                                                                       │  │
│  │ • Lifespan Events:                                                   │  │
│  │   - Setup Phoenix observability                                      │  │
│  │   - Connect to MongoDB                                               │  │
│  │   - Initialize repositories                                          │  │
│  │   - Auto-load restaurants                                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                       │                                                     │
│                       │ Service Layer                                       │
│                       ▼                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Services (Business Logic)                                            │  │
│  │                                                                       │  │
│  │ • RestaurantService → RestaurantRepository                           │  │
│  │ • FoodService → FoodRepository                                       │  │
│  │ • HybridSearchService (generic for both)                             │  │
│  │   - OpenAI embedding generation                                      │  │
│  │   - MongoDB vector search                                            │  │
│  │   - BAAI reranker application                                        │  │
│  │   - Result aggregation                                               │  │
│  │                                                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                       │                                                     │
│                       │ Repository Layer                                    │
│                       ▼                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Repositories (Data Access)                                           │  │
│  │                                                                       │  │
│  │ • MongoRestaurantRepository                                          │  │
│  │ • MongoFoodRepository                                                │  │
│  │ • MongoUserRepository                                                │  │
│  │                                                                       │  │
│  │ Aggregation Pipelines:                                               │  │
│  │ - $geoNear (location filtering)                                      │  │
│  │ - $match (dietary, allergen safety)                                  │  │
│  │ - $vectorSearch (semantic similarity)                                │  │
│  │ - $addFields (scoring)                                               │  │
│  │ - $sort (relevance ranking)                                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                       │                                                     │
│                       │                                                     │
└───────────────────────┼─────────────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────────────────┐
│                      MONGODB ATLAS                                           │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Database: vybe                                                       │  │
│  │                                                                       │  │
│  │ Collections:                                                          │  │
│  │ • restaurants (with vector_embeddings, geospatial index)             │  │
│  │ • food (with vector_embeddings, allergen safety)                     │  │
│  │ • users (preferences, dietary restrictions)                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Vector Search Indexes:                                                      │
│  • restaurants.restaurant_vector_index (1536-dim OpenAI embeddings)         │
│  • food.food_vector_index (1536-dim OpenAI embeddings)                      │
│                                                                              │
│  Geospatial Indexes:                                                         │
│  • restaurants.location_2dsphere                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Example: User Query

### User: "Find vegan restaurants near me"

**Step 1: Frontend (MCP Client)**
```javascript
// User types query in SearchChat component
userQuery = "Find vegan restaurants near me"

// Frontend MCP client sends to AI Agent:
{
  "query": "Find vegan restaurants near me",
  "tools": [
    {
      "name": "search_restaurants_vector",
      "description": "Search restaurants using semantic AI-powered search",
      "inputSchema": { ... }
    },
    ... (3 more tools)
  ]
}
```

**Step 2: AI Agent (AI Developer)**
```python
# AI Agent receives tools + query
# Passes to Claude via CrewAI/LangGraph

# Claude decides: "I need to search for vegan restaurants"
# Claude calls tool: search_restaurants_vector
# with params: {"query": "vegan restaurants near me"}
```

**Step 3: MCP Server (Vybesix-MCP)**
```python
# Vybesix-MCP receives tool call
# Executes: search_restaurants_vector(query="vegan restaurants near me")
# Makes HTTP POST to: http://localhost:8000/api/v1/restaurants/vector-search
```

**Step 4: Backend API**
```python
# POST /api/v1/restaurants/vector-search
# Request body: {"query": "vegan restaurants near me"}

# RestaurantService + HybridSearchService:
# 1. Generate embedding: OpenAI(query) → 1536-dim vector
# 2. MongoDB $vectorSearch: find similar restaurants
# 3. BAAI reranker: score and rank results
# 4. Return top results
```

**Step 5: MongoDB**
```javascript
// Aggregation Pipeline:
[
  { $vectorSearch: { queryVector: [...], limit: 100 } },
  { $match: { dietary: "vegan" } },
  { $addFields: { score: ... } },
  { $sort: { score: -1 } }
]

// Returns: [Vegan Kitchen, Pure Joy Bistro, Plant Paradise]
```

**Step 6: Results Return**
```
Backend API → Vybesix-MCP → AI Agent → Frontend → User Display
```

---

## Component Responsibilities

### Backend (✅ Complete)
- **Database Layer**: PyMongo AsyncMongoClient, aggregation pipelines
- **Service Layer**: Business logic, preference injection, ranking
- **API Layer**: FastAPI endpoints with Pydantic validation
- **MCP Server**: FastMCP tool definitions that call backend APIs
- **Observability**: Arize Phoenix + OpenTelemetry tracing

**Key Files:**
- `backend/app/main.py` - FastAPI application
- `backend/app/services/` - Business logic
- `backend/app/repositories/` - MongoDB data access
- `vybesix-mcp/src/vybesix_mcp/server.py` - MCP tools

### Frontend (🔄 In Progress)
- **MCP Client**: Connect to vybesix-mcp via stdio
- **Tool Discovery**: List available tools from MCP server
- **Query Interface**: User input form for searches
- **Tool Passing**: Send tools + query to AI Agent
- **Result Display**: Show recommendations from AI Agent

**Key Files:**
- `frontend/src/hooks/useMCPClient.js` - MCP client hook
- `frontend/src/components/SearchChat.jsx` - Main search component

**Reference:** `FRONTEND_MCP_CLIENT_GUIDE.md`

### AI Agent (🔄 In Progress)
- **Tool Reception**: Receive tool definitions from frontend
- **LLM Integration**: Bind tools to Claude via CrewAI/LangGraph
- **Decision Making**: Claude decides which tools to use
- **Tool Execution**: Call tools via backend/MCP APIs
- **Response Generation**: Synthesize results for frontend

**Reference:** `AI_DEV_GUIDE.md`

---

## Communication Protocols

| Sender | Receiver | Protocol | Format |
|--------|----------|----------|--------|
| Frontend | Vybesix-MCP | **Stdio (MCP)** | Binary (MessagePack) |
| Frontend | AI Agent | **HTTP/REST** | JSON |
| AI Agent | Claude | **OpenAI API** | JSON |
| Vybesix-MCP | Backend | **HTTP/REST** | JSON |
| Backend | MongoDB | **MongoDB Wire Protocol** | BSON |

---

## Development Environment

### Local Setup

```bash
# Terminal 1: Backend
cd backend
uv run uvicorn app.main:app --reload
# Running on http://localhost:8000

# Terminal 2: Vybesix-MCP
cd vybesix-mcp
uv run python -m vybesix_mcp.server
# Listening for MCP connections (stdio)

# Terminal 3: AI Agent
cd agents
python src/restaurant_agent.py
# Running on http://localhost:8001

# Terminal 4: Frontend
cd frontend
npm run dev
# Running on http://localhost:5173
```

### Observability

```bash
# Phoenix Dashboard
http://localhost:6006
# Shows:
# - HTTP request traces (backend)
# - Embedding generation latency (OpenAI)
# - Reranker latency (BAAI)
# - End-to-end query performance
```

---

## Deployment Architecture

```
docker-compose.yml orchestrates:

1. phoenix-observability (Arize Phoenix official image)
   - Port: 6006
   
2. backend (built from backend/Dockerfile)
   - Port: 8000
   - Environment: PHOENIX_COLLECTOR_ENDPOINT=http://phoenix-observability:6006/v1/traces
   - Depends on: phoenix-observability
   
3. mcp-server (built from vybesix-mcp/Dockerfile)
   - Port: 5000 (for HTTP fallback)
   - Environment: API_BASE_URL=http://backend:8000
   - Depends on: backend
   
4. frontend (built from frontend/Dockerfile)
   - Port: 3000
   - Environment: VITE_API_URL=http://backend:8000
   
5. agents (built from agents/Dockerfile)
   - Port: 8001
   - Depends on: backend
```

---

## Data Models

### Restaurant Entity
```json
{
  "restaurant_id": "1",
  "name": "Purely Vegan Hub",
  "location": { "type": "Point", "coordinates": [lon, lat] },
  "cuisine": ["vegan", "healthy"],
  "dietary": ["vegan", "vegetarian"],
  "price_level": 2,
  "rating": 4.5,
  "has_parking": true,
  "has_live_music": false,
  "service_hours": [{ "open": 480, "close": 1080 }],
  "vector_embeddings": [0.123, -0.456, ...] // 1536-dim
}
```

### Food Entity
```json
{
  "food_id": "101",
  "restaurant_id": "1",
  "name": "Buddha Bowl",
  "description": "Quinoa, roasted veggies, tahini dressing",
  "category": "main",
  "cuisine": ["vegan"],
  "dietary": ["vegan", "gluten-free"],
  "allergens": [],
  "prep_time_minutes": 15,
  "price": 12.99,
  "vector_embeddings": [0.234, -0.567, ...] // 1536-dim
}
```

---

## Key Decisions

### Why Stdio MCP over HTTP?
- **Standard MCP protocol** - works with Claude Code, IDE extensions
- **Secure** - no network exposure
- **Efficient** - binary message format
- **Tool discovery** - automatic tool definition sharing

### Why Generic HybridSearchService?
- **Reusable** - works for both restaurants and food
- **Consistent** - same ranking algorithm
- **Maintainable** - single implementation
- **Extensible** - add new entity types without duplication

### Why BAAI Reranker?
- **Better than MS-MARCO** for semantic similarity
- **Production-ready** - optimized model size
- **Fast** - 300-400MB, runs on CPU
- **Flexible** - works with any search results

### Why Hard Allergen Filtering at DB Level?
- **Safety first** - filtered before any other processing
- **Efficient** - MongoDB handles filtering
- **Guaranteed** - no way to accidentally include allergens
- **Auditable** - clear filtering logic in query

---

## Integration Checklist

- [x] **Backend**: APIs + MCP Server (complete)
- [ ] **Frontend**: MCP Client + Tool Discovery
- [ ] **Frontend**: Query interface + result display
- [ ] **AI Agent**: Tool reception + orchestration
- [ ] **AI Agent**: Claude integration
- [ ] **End-to-End Testing**: Full user query flow
- [ ] **Docker Deployment**: Multi-container orchestration
- [ ] **Observability**: Phoenix dashboard verification

---

## Documentation Files

- **README.md** - Quick start, setup, testing
- **CLAUDE.md** - Project guidelines and architecture
- **Deployment.md** - Docker build and shared workspace setup
- **ARCHITECTURE.md** - This file
- **FRONTEND_MCP_CLIENT_GUIDE.md** - Frontend MCP client implementation
- **AI_DEV_GUIDE.md** - AI Agent + Claude integration

---

## Support & Troubleshooting

See README.md troubleshooting section for common issues.

For architecture questions, see the respective developer guides:
- Frontend issues → FRONTEND_MCP_CLIENT_GUIDE.md
- AI Agent issues → AI_DEV_GUIDE.md
- Backend issues → README.md
