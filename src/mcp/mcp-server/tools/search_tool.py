from mcp_server import mcp
from tavily import TavilyClient

@mcp.tool()
def search_tool(query: str) -> str:
    """
    Search the web for relevant information using Tavily Search.

    Args:
        query (str): The search query string.

    Returns:
        dict: A dictionary of search results obtained from Tavily search.
    """
    try:
        # NOTE: You need to set the TAVILY_API_KEY environment variable to use this tool.
        tavily_client = TavilyClient()
        response = tavily_client.search(query=query, max_results=5, include_answer=True)
        return response
    except Exception as e:
        # Log the exception or handle it as needed
        return f"An error occurred while while invoking the tool Tavily search tool. Here is the logs, try to analyze it and retry invoking the tool possibly with different payload. Logs: {str(e)}"