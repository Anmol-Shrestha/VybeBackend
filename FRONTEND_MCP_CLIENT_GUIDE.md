# Frontend MCP Client Setup Guide

## Overview

Your React frontend acts as an **MCP Client** that:
1. Connects to the vybesix-mcp server (tool provider)
2. Discovers available tools (search_restaurants_vector, search_food_vector, etc.)
3. Sends tools + user query to the AI Agent
4. Displays results from the AI Agent

```
User Input → Frontend (MCP Client) → Vybesix-MCP Server → AI Agent → Claude → Results
```

---

## Prerequisites

- Node.js 18+ with npm
- `@modelcontextprotocol/sdk` package
- Running vybesix-mcp server
- Running AI Agent service

---

## Installation

Install the MCP client SDK:

```bash
cd frontend
npm install @modelcontextprotocol/sdk
```

---

## Step 1: Create MCP Client Hook

Create `frontend/src/hooks/useMCPClient.js`:

```javascript
import { useState, useEffect } from 'react';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

export function useMCPClient() {
  const [client, setClient] = useState(null);
  const [tools, setTools] = useState([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const initializeMCP = async () => {
      try {
        // Create transport (spawns vybesix-mcp process)
        const transport = new StdioClientTransport({
          command: 'uv',
          args: ['run', 'python', '-m', 'vybesix_mcp.server'],
          cwd: '../vybesix-mcp' // Path to vybesix-mcp directory
        });

        // Create client and connect
        const mcpClient = new Client({
          name: 'vybesix-frontend',
          version: '1.0.0'
        }, {
          capabilities: {}
        });

        await mcpClient.connect(transport);

        // List available tools from server
        const toolList = await mcpClient.listTools();
        setTools(toolList.tools || []);
        setClient(mcpClient);
        setConnected(true);

        console.log('✅ MCP Client connected. Available tools:');
        toolList.tools?.forEach(tool => {
          console.log(`  - ${tool.name}`);
        });
      } catch (err) {
        setError(err.message);
        console.error('❌ MCP Client connection failed:', err);
      }
    };

    initializeMCP();

    return () => {
      client?.close();
    };
  }, []);

  return { client, tools, connected, error };
}
```

---

## Step 2: Use MCP Client in Component

Create `frontend/src/components/SearchChat.jsx`:

```javascript
import { useState } from 'react';
import { useMCPClient } from '../hooks/useMCPClient';

export function SearchChat() {
  const { client, tools, connected, error } = useMCPClient();
  const [userQuery, setUserQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!client || !userQuery.trim()) return;

    setLoading(true);
    try {
      // Send query + available tools to AI Agent
      const response = await fetch('http://localhost:8001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userQuery,
          tools: tools.map(tool => ({
            name: tool.name,
            description: tool.description,
            inputSchema: tool.inputSchema
          }))
        })
      });

      const data = await response.json();
      setResults(data);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  if (error) {
    return <div className="error">❌ MCP Connection Error: {error}</div>;
  }

  return (
    <div className="search-container">
      <div className="status">
        {connected ? '✅ Connected to tools' : '⏳ Connecting...'}
      </div>

      <form onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search restaurants or food..."
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
          disabled={!connected}
        />
        <button type="submit" disabled={!connected || loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {results && (
        <div className="results">
          <h3>Results:</h3>
          <pre>{JSON.stringify(results, null, 2)}</pre>
        </div>
      )}

      {tools.length > 0 && (
        <details>
          <summary>Available Tools ({tools.length})</summary>
          <ul>
            {tools.map(tool => (
              <li key={tool.name}>
                <strong>{tool.name}</strong>: {tool.description}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
```

---

## Step 3: Send Tools to AI Agent

When frontend discovers tools, send them to the AI Agent:

```javascript
// Frontend → AI Agent
POST /api/chat
{
  "query": "Find vegan restaurants near me",
  "location": { "lat": 43.6629, "lng": -79.3957 },
  "tools": [
    {
      "name": "search_restaurants_vector",
      "description": "Search restaurants using semantic AI-powered search",
      "inputSchema": { ... }
    },
    {
      "name": "search_food_vector",
      "description": "Search food items using semantic AI-powered search",
      "inputSchema": { ... }
    },
    // ... other tools
  ]
}
```

---

## Step 4: Receive Results from AI Agent

AI Agent orchestrates tool calls and returns results:

```javascript
// AI Agent → Frontend
{
  "status": "success",
  "reasoning": "User asked for vegan restaurants, using semantic search",
  "toolCalls": [
    {
      "tool": "search_restaurants_vector",
      "params": {
        "query": "vegan restaurants",
        "restaurant_ids": ["1", "2", "3"]
      },
      "result": [ ... restaurant results ... ]
    }
  ],
  "finalAnswer": "Found 5 vegan-friendly restaurants in your area..."
}
```

---

## Running the Frontend

```bash
cd frontend

# Terminal 1: Start vybesix-mcp server
cd ../vybesix-mcp
uv run python -m vybesix_mcp.server

# Terminal 2: Start frontend
npm run dev
```

---

## Troubleshooting

**"MCP Connection failed"**
- Ensure vybesix-mcp is running and reachable
- Check that `API_BASE_URL` environment variable points to backend (default: http://localhost:8000)
- Verify backend API endpoints are working: `curl http://localhost:8000/api/v1/restaurants/search`

**"Tools not loading"**
- Check browser console for errors
- Verify MCP server is exposing tools: `uv run python -m vybesix_mcp.server --debug`

**"AI Agent not responding"**
- Ensure AI Agent service is running on correct port (e.g., localhost:8001)
- Verify tools are being sent correctly in request payload

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (React)                                             │
│ ┌──────────────────┐                                        │
│ │ MCP Client       │─ connects to ─→ Vybesix-MCP Server     │
│ │ (useMCPClient)   │   (stdio)        (4 tools)             │
│ └──────────────────┘                                        │
│       │                                                      │
│       │ discovers tools                                     │
│       ↓                                                      │
│ ┌──────────────────┐                                        │
│ │ SearchChat       │                                        │
│ │ Component        │─ sends query + tools ──→ AI Agent     │
│ └──────────────────┘                         (runs Claude)  │
│       │                                            │         │
│       └─ displays results ←─────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. Implement useMCPClient hook in your React app
2. Update backend .env with correct API_BASE_URL
3. Ensure vybesix-mcp server is running
4. Connect to AI Agent service (see AI_DEV_GUIDE.md)