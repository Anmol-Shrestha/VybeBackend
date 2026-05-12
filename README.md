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

Run backend tests:
```bash
cd backend
pipenv run pytest
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
