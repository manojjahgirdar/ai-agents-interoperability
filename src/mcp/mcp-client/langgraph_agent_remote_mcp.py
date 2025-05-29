from langchain_openai import ChatOpenAI
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
import asyncio
import os
import logging

# Set up logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'ERROR'))
logger = logging.getLogger(__name__)

if os.getenv('OPENAI_API_KEY'):
    llm = ChatOpenAI(model="o3-mini")
else:
    print('Export OPENAI_API_KEY to initialize OpenAI LLM.')
    exit(1)

@asynccontextmanager
async def main():
    client = MultiServerMCPClient({
        "mcp_server": {
            "url": os.getenv("REMOTE_MCP_URL", "http://localhost:8000/sse"),
            "transport": "sse"
            }
        })
    tools = await client.get_tools()
    # Filter tools to include only the necessary ones for itinerary planning
    tools = [tool for tool in tools if tool.name in ["search_tool", "weather_tool"]]

    logger.info("Loaded MCP tools:" + ", ".join(tool.name for tool in tools))

    agent = create_react_agent(
            llm,
            tools=tools,
            prompt="You are a helpful assistant."
        )
    
    yield agent

async def invoke_agent(query):
    async with main() as agent:
        agent_response = await agent.ainvoke({"messages": query})
        print("==== Final Answer ====")
        print(agent_response['messages'][-1].content)


if __name__ == "__main__":
    
    query = "Give me 5 tourist attractions and weather details for Bengaluru"
    asyncio.run(invoke_agent(query=query))
