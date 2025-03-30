from mcp_server import mcp
from langchain_community.tools import DuckDuckGoSearchRun
import os

@mcp.tool()
def search_tool(query: str) -> str:
    """
    Search the web for relevant information using DuckDuckGo Search.

    Args:
        query (str): The search query string.

    Returns:
        dict: A dictionary of search results obtained from DuckDuckGo search.
    """
    try:
        search = DuckDuckGoSearchRun()
        response = search.invoke(query)
        return response
    except Exception as e:
        # Log the exception or handle it as needed
        return f"An error occurred while while invoking the tool DuckDuckGo search tool. Here is the logs, try to analyze it and retry invoking the tool possibly with different payload. Logs: {str(e)}"