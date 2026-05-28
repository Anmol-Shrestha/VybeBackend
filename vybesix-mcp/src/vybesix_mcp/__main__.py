"""Entry point for running the Vybesix MCP server as a Python module."""

from vybesix_mcp.server import mcp


if __name__ == "__main__":
    mcp.run()
