"""Tests for the Vybesix MCP Server."""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vybesix_mcp.server import server, list_tools


@pytest.mark.asyncio
async def test_server_initialization():
    """Test that server initializes correctly."""
    assert server.name == "vybesix-mcp"


@pytest.mark.asyncio
async def test_list_tools():
    """Test that tools are properly defined."""
    tools = await list_tools()
    assert len(tools) == 2

    tool_names = {tool["name"] for tool in tools}
    assert "search_restaurants_manual" in tool_names
    assert "search_restaurants_vector" in tool_names


@pytest.mark.asyncio
async def test_manual_search_tool_schema():
    """Test manual search tool has proper schema."""
    tools = await list_tools()
    manual_tool = next(t for t in tools if t["name"] == "search_restaurants_manual")

    schema = manual_tool["inputSchema"]
    assert schema["type"] == "object"
    assert "latitude" in schema["properties"]
    assert "longitude" in schema["properties"]
    assert schema["required"] == ["latitude", "longitude"]


@pytest.mark.asyncio
async def test_vector_search_tool_schema():
    """Test vector search tool has proper schema."""
    tools = await list_tools()
    vector_tool = next(t for t in tools if t["name"] == "search_restaurants_vector")

    schema = vector_tool["inputSchema"]
    assert schema["type"] == "object"
    assert "query" in schema["properties"]
    assert "restaurant_ids" in schema["properties"]
    assert set(schema["required"]) == {"query", "restaurant_ids"}