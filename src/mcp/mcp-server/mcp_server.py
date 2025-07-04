# Import depdendencies
from mcp.server.fastmcp import FastMCP

# Server created
mcp = FastMCP("Utility Tools")

# Import all the tools
from tools import *

if __name__ == "__main__":
    mcp.run(transport="sse") # change the transport to "sse" to deploy as remote MCP server
