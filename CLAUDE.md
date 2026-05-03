# Project: Restaurant Search MVP
## Tech Stack
- Frontend: React (Vite) + Tailwind CSS
- Backend: FastAPI (Python 3.11+)
- Database: MongoDB Atlas (Motor for async)
- Tooling: Pipenv

## Architecture
- Pattern: Service-Layer / Repository / Adapter
- Directory Structure:
  - `/backend/src/api`: Routes
  - `/backend/src/services`: Business Logic (The Chef)
  - `/backend/src/repositories`: Database Logic (The Pantry)
  - `/backend/src/models`: Pydantic Schemas (The Contract)

## Guidelines
- Follow Top-Down Design.
- Use Dependency Injection for repositories into services.
- Backend must have Pytest for Service-layer logic.