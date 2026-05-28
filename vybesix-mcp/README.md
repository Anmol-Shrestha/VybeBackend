# Vybesix MCP Server

An MCP (Model Context Protocol) server that exposes the Vybesix Restaurant Discovery API as tools for AI agents.

## Setup

### Prerequisites
- Python 3.11+
- `uv` package manager

### Installation

1. Clone the repository and navigate to this directory:
```bash
cd vybesix-mcp
```

2. Create a `.env` file:
```bash
cp .env.example .env
```

3. Install dependencies using `uv`:
```bash
uv sync
```

## Available Tools

### 1. `search_restaurants_manual`
Structured search using location and preferences.

**Parameters:**
- `latitude` (required): User's latitude
- `longitude` (required): User's longitude
- `radius_km`: Search radius in km (default: 5)
- `meal_types`: List of meal types (breakfast, lunch, dinner)
- `cuisine`: List of cuisines (italian, vegan, mexican, etc.)
- `dietary`: Dietary restrictions (vegan, gluten-free, halal, kosher)
- `price_max`: Maximum price level (1-4)
- `min_rating`: Minimum rating (0-5, default: 0.0)
- `min_capacity`: Minimum seating capacity (default: 1)
- `has_parking`: Must have parking (default: false)
- `has_live_music`: Must have live music (default: false)
- `userID`: User ID for preference injection (optional)

**Example:**
```json
{
  "latitude": 43.6532,
  "longitude": -79.3832,
  "radius_km": 10,
  "dietary": ["vegan"],
  "cuisine": ["italian"]
}
```

### 2. `search_restaurants_vector`
AI-powered semantic search using natural language.

**Parameters:**
- `query` (required): Natural language query
- `restaurant_ids` (required): List of restaurant IDs to search within
- `limit`: Number of results to return (default: 10)
- `num_candidates`: Number of candidates to rerank (default: 100)

**Example:**
```json
{
  "query": "cozy vegan restaurant with live music near downtown",
  "restaurant_ids": ["rest_001", "rest_002", "rest_003"],
  "limit": 5
}
```

## Running the Server

### Using the MCP client in Claude
Configure your Claude Code settings to use this MCP server:

```json
{
  "mcpServers": {
    "vybesix": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/vybesix-mcp", "src/vybesix_mcp/server.py"]
    }
  }
}
```

Or run directly:
```bash
uv run src/vybesix_mcp/server.py
```

## Testing with Claude

1. Start your backend server:
```bash
# In the backend directory
pipenv run uvicorn app.main:app --reload --port 8000
```

2. Configure the MCP server in Claude Code settings

3. Ask Claude questions like:
   - "Search for vegan restaurants near 43.6532, -79.3832"
   - "Find restaurants with Italian cuisine within 5km"
   - "Using vector search, find cozy dinner spots with live music"

## Development

### Running Tests
```bash
uv run pytest tests/
```

### Project Structure
```
vybesix-mcp/
├── src/vybesix_mcp/
│   ├── __init__.py
│   └── server.py          # Main MCP server
├── pyproject.toml         # Project config and dependencies
├── uv.lock               # Locked dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Architecture Notes

- **Async Design**: Full async/await support for concurrent requests
- **Error Handling**: Graceful error responses for API failures and validation errors
- **Tool Schema**: Properly defined JSON schemas for each tool
- **Request Validation**: Pydantic models validate inputs before sending to API

## Next Steps

After validating this MCP server:
1. Build MCP tools for the Food Search Service endpoints
2. Integrate with CrewAI for multi-agent orchestration
3. Add monitoring and logging