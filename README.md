# Restaurant Search MVP

A full-stack restaurant search application with FastAPI backend and React frontend.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Pipenv: `pip install pipenv`
- MongoDB Atlas account (free tier available)

### Setup

1. **Configure MongoDB Connection**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your MongoDB Atlas credentials
   ```

2. **Start both services**
   ```bash
   ./start.sh
   ```

   This will:
   - Install Pipenv dependencies (backend)
   - Install npm dependencies (frontend)
   - Start the FastAPI backend on `http://localhost:8000`
   - Start the Vite dev server on `http://localhost:5173`

### Manual Start (if preferred)

**Backend:**
```bash
cd backend
pipenv install --dev
pipenv run python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # Routes
│   │   ├── services/     # Business Logic
│   │   ├── repositories/ # Database Logic
│   │   ├── models/       # Pydantic Schemas
│   │   └── main.py       # FastAPI app
│   ├── tests/            # Pytest tests
│   ├── Pipfile           # Python dependencies
│   └── .env.example      # Environment template
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
└── start.sh              # Start both services
```

## Development

### Backend
- FastAPI for API endpoints
- Motor for async MongoDB operations
- Pytest for testing
- Service-layer architecture with dependency injection

### Frontend
- React + Vite for fast development
- Tailwind CSS for styling
- Vite HMR for hot module replacement

## Testing

### Test Files

The backend includes comprehensive test coverage for the RAG pipeline and restaurant discovery service:

| Test File | Purpose |
|-----------|---------|
| `test_restaurant_service.py` | Integration tests for RestaurantService with preference injection and geospatial search |
| `test_hybrid_search_service.py` | Tests for HybridSearchService with OpenAI embeddings and MongoDB vector search |
| `test_vector_similarity.py` | Validates embedding quality and cosine similarity scores for semantic search queries |
| `conftest.py` | Pytest fixtures and MongoDB connection setup for async tests |

### Running Tests

**Prerequisites:**
- MongoDB Atlas connection (MONGODB_URL env var)
- OpenAI API key (OPENAI_API_KEY env var)
- Database seeded with test data

**Run all tests:**
```bash
cd backend
pipenv run pytest
```

**Run specific test file:**
```bash
pipenv run pytest test/test_restaurant_service.py -v
```

**Run with coverage:**
```bash
pipenv run pytest --cov=app --cov-report=html
```

**Run a specific test:**
```bash
pipenv run pytest test/test_restaurant_service.py::test_restaurant_search_with_preference_injection -v
```

**Run vector similarity validation:**
```bash
pipenv run python test/test_vector_similarity.py
```

### Environment Setup for Testing

Create a `.env` file in the `backend/` directory with:
```
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
OPENAI_API_KEY=sk-...
DATABASE_NAME=vybe
```

**Note:** Tests require a running MongoDB Atlas connection and seeded restaurant data.

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`




## Seeding MongoDB Collection for resturants
1. The preprocessing of JSON data is in the script
2. Any PDF file can be extracted into JSON and that can be transformed and sent to the seed_restaurants.py
3. JSON -> MongoDB Atlas