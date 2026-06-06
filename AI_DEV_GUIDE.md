# AI Developer Guide: Receiving Tools from Frontend

## Overview

Your AI Agent receives tool definitions from the frontend MCP client and orchestrates their usage:

```
Frontend (MCP Client)
    ↓ sends tools + user query
AI Agent (CrewAI/LangGraph)
    ↓ receives tool definitions
Claude LLM
    ↓ decides which tools to use
Tool Execution
    ↓
Results → Frontend
```

---

## Architecture

**Tool Flow:**
1. Frontend MCP Client connects to vybesix-mcp server
2. Frontend discovers 4 tools:
   - `search_restaurants_manual`
   - `search_restaurants_vector`
   - `search_food_manual`
   - `search_food_vector`
3. Frontend sends tools + user query to AI Agent API
4. AI Agent registers tools with Claude
5. Claude uses tools to fulfill request
6. Results returned to frontend

---

## Receiving Tools from Frontend

### API Endpoint

Your AI Agent should expose an endpoint:

```
POST /api/chat
{
  "query": "Find vegan restaurants near me",
  "location": { "lat": 43.6629, "lng": -79.3957 },
  "tools": [
    {
      "name": "search_restaurants_vector",
      "description": "Search restaurants using semantic AI-powered search",
      "inputSchema": {
        "type": "object",
        "properties": {
          "query": { "type": "string" },
          "restaurant_ids": { "type": "array" },
          "limit": { "type": "integer" }
        },
        "required": ["query"]
      }
    },
    ... more tools ...
  ]
}
```

### Response Format

```json
{
  "status": "success",
  "reasoning": "User asked for vegan restaurants, using vector search",
  "toolCalls": [
    {
      "tool": "search_restaurants_vector",
      "params": {
        "query": "vegan restaurants near me",
        "restaurant_ids": ["1", "2", "3"]
      },
      "result": [ ... results ... ]
    },
    {
      "tool": "search_food_vector",
      "params": {
        "query": "vegan dishes",
        "restaurant_ids": ["1"]
      },
      "result": [ ... results ... ]
    }
  ],
  "finalAnswer": "I found 3 vegan-friendly restaurants with excellent vegan options..."
}
```

---

## Implementation: CrewAI Example

Create `agents/src/restaurant_agent.py`:

```python
"""Restaurant discovery agent using CrewAI and Claude."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import json

app = FastAPI()

class ToolDefinition(BaseModel):
    """Tool definition from frontend."""
    name: str
    description: str
    inputSchema: dict

class ChatRequest(BaseModel):
    """Chat request from frontend."""
    query: str
    tools: list[ToolDefinition]
    location: Optional[dict] = None
    restaurant_ids: Optional[list[str]] = None

class ChatResponse(BaseModel):
    """Chat response to frontend."""
    status: str
    reasoning: str
    toolCalls: list[dict]
    finalAnswer: str

# Initialize Claude
llm = ChatOpenAI(model="claude-3-5-sonnet-20241022", temperature=0)

# Tool execution map (maps tool names to functions)
async def execute_tool(tool_name: str, params: dict) -> Any:
    """Execute tool by calling vybesix-mcp server."""
    # This would typically call the MCP server or backend API
    # For now, we'll mock the response
    
    if tool_name == "search_restaurants_vector":
        return {
            "results": [
                {
                    "restaurant_id": "1",
                    "name": "Purely Vegan Hub",
                    "description": "All-vegan restaurant"
                }
            ]
        }
    elif tool_name == "search_food_vector":
        return {
            "results": [
                {
                    "food_id": "1",
                    "name": "Vegan Buddha Bowl",
                    "restaurant_id": "1"
                }
            ]
        }
    # Add other tools as needed
    return {"error": "Tool not found"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process user query using available tools.
    
    1. Register tools with Claude
    2. Let Claude decide which tools to use
    3. Execute tools
    4. Return results
    """
    try:
        # Step 1: Create agent with tools
        agent = Agent(
            role="Restaurant Discovery Expert",
            goal=f"Help user find the best restaurants and food items based on: {request.query}",
            backstory="You are an expert at understanding restaurant and food preferences. "
                     "Use the available tools to search and discover the perfect options.",
            llm=llm,
            tools=[],  # Tools will be managed manually
            verbose=True
        )

        # Step 2: Create task
        task = Task(
            description=f"""
            User query: {request.query}
            
            Available tools:
            {json.dumps([
                {
                    "name": tool.name,
                    "description": tool.description
                }
                for tool in request.tools
            ], indent=2)}
            
            Location: {request.location}
            
            Use the appropriate tools to find restaurants and food items.
            Analyze results and provide personalized recommendations.
            """,
            agent=agent,
            expected_output="Detailed recommendations with reasoning"
        )

        # Step 3: Execute crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )

        result = crew.kickoff()

        # Step 4: Parse and structure response
        tool_calls = []
        # You would parse Claude's response to extract actual tool calls
        # For now, this is a simplified example
        
        return ChatResponse(
            status="success",
            reasoning="User asked for restaurants, analyzing preferences...",
            toolCalls=tool_calls,
            finalAnswer=str(result)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

## Implementation: LangGraph Example

Create `agents/src/langraph_agent.py`:

```python
"""Restaurant discovery agent using LangGraph."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Optional
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
import json

app = FastAPI()

class ChatRequest(BaseModel):
    query: str
    tools: list[dict]
    location: Optional[dict] = None

# Initialize Claude
llm = ChatOpenAI(model="claude-3-5-sonnet-20241022")

# Tool execution
async def call_tool(tool_name: str, params: dict) -> str:
    """Execute tool."""
    # Call vybesix-mcp server or backend API
    return json.dumps({"result": f"Tool {tool_name} called with {params}"})

# Define agent graph
graph = StateGraph(dict)

def route_tools(state):
    """Route to tool execution."""
    messages = state.get("messages", [])
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

def process_tools(state):
    """Execute tools and add results."""
    messages = state["messages"]
    tool_results = []
    
    # Process each tool call from Claude
    for tool_call in messages[-1].tool_calls:
        result = await call_tool(tool_call["name"], tool_call["args"])
        tool_results.append(ToolMessage(
            content=result,
            tool_call_id=tool_call["id"]
        ))
    
    return {"messages": messages + tool_results}

def agent_node(state):
    """Claude agent node."""
    messages = state["messages"]
    
    # Bind tools to Claude
    tools_list = state.get("tools", [])
    bound_llm = llm.bind_tools(tools_list)
    
    response = bound_llm.invoke(messages)
    return {"messages": messages + [response]}

# Build graph
graph.add_node("agent", agent_node)
graph.add_node("tools", process_tools)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", route_tools)
graph.add_edge("tools", "agent")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Process query with tool-using agent."""
    try:
        # Initialize state
        state = {
            "messages": [HumanMessage(content=request.query)],
            "tools": request.tools
        }
        
        # Run graph
        result = graph.invoke(state)
        
        # Extract final response
        final_message = result["messages"][-1]
        
        return {
            "status": "success",
            "finalAnswer": final_message.content,
            "toolCalls": []  # Extract from message history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

## Tool Schema From Frontend

When frontend sends tools, they will have this structure:

```json
{
  "name": "search_restaurants_vector",
  "description": "Search restaurants using semantic AI-powered search",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Natural language search query"
      },
      "restaurant_ids": {
        "type": "array",
        "items": { "type": "string" },
        "description": "List of restaurant IDs to search within"
      },
      "limit": {
        "type": "integer",
        "description": "Number of results to return"
      },
      "num_candidates": {
        "type": "integer",
        "description": "Number of candidates to rerank"
      }
    },
    "required": ["query"]
  }
}
```

**Use this schema to:**
1. Validate Claude's tool calls
2. Generate type hints
3. Create tool wrappers in your agent framework

---

## Executing Tools

When Claude decides to use a tool, execute it via the backend:

```python
async def execute_mcp_tool(tool_name: str, params: dict):
    """Execute tool via backend or MCP server."""
    # Option 1: Call backend API directly
    async with httpx.AsyncClient() as client:
        if tool_name == "search_restaurants_vector":
            response = await client.post(
                "http://localhost:8000/api/v1/restaurants/vector-search",
                json={
                    "query": params["query"],
                    "num_candidates": params.get("num_candidates", 100)
                }
            )
        elif tool_name == "search_food_vector":
            response = await client.post(
                "http://localhost:8000/api/v1/food/vector-search",
                json={
                    "query": params["query"],
                    "restaurant_ids": params.get("restaurant_ids"),
                    "num_candidates": params.get("num_candidates", 100)
                }
            )
        
        return response.json()
```

---

## Development Setup

```bash
# Install dependencies
cd agents
pip install fastapi uvicorn crewai langraph langgraph-checkpoint

# Start agent server
python src/restaurant_agent.py
# Server running on http://localhost:8001
```

---

## Testing the Integration

```bash
# Terminal 1: Start backend
cd backend
uv run uvicorn app.main:app --reload

# Terminal 2: Start vybesix-mcp
cd vybesix-mcp
uv run python -m vybesix_mcp.server

# Terminal 3: Start AI agent
cd agents
python src/restaurant_agent.py

# Terminal 4: Start frontend
cd frontend
npm run dev

# Test in browser: http://localhost:5173
```

---

## Debugging

**Enable Claude tool use logging:**
```python
llm = ChatOpenAI(
    model="claude-3-5-sonnet-20241022",
    temperature=0,
    verbose=True  # See tool calls
)
```

**Check tool execution:**
```python
# Log each tool call
for tool_call in message.tool_calls:
    print(f"Tool: {tool_call['name']}")
    print(f"Args: {tool_call['args']}")
```

**Verify frontend-agent communication:**
```bash
# Check if frontend is sending tools
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "vegan restaurants", "tools": []}'
```

---

## Next Steps

1. Choose CrewAI or LangGraph (or another framework)
2. Implement agent endpoint
3. Connect to backend APIs for tool execution
4. Test with frontend MCP client
5. Deploy agent service to docker-compose
