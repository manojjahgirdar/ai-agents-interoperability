import json
import logging
from main import Context, RunYield, RunYieldResume, server, Message, MessagePart
from functools import reduce
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from collections.abc import AsyncGenerator
from langchain_openai import ChatOpenAI
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
import os

# Set up logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'ERROR'))
logger = logging.getLogger(__name__)

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o")

# Define Memory
memory = MemorySaver()

# Define System Prompt
system_prompt = (
    "You are a itinerary provider agent.",
    "With the given tools, gather the tourist attractions and weather details for the city.",
    "Create a travel itinerary with Top 5 tourist attractions and weather details.",
    "Respond in a structured markdown format."
)

system_prompt = "\n".join(system_prompt)

@asynccontextmanager
async def create_agent():
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
            prompt=system_prompt,
            checkpointer=memory
        )
    
    yield agent

@server.agent()
async def itinerary_provider_agent(inputs: list[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """An itinerary provider agent that uses the LangGraph framework to gather information about tourist attractions and weather details for a given city using the web search tool and weather tool."""
    query = reduce(lambda x, y: x + y, inputs)
    logger.info(json.dumps(
        {
            "session_id": str(context.session_id),
            "prompt": str(query)
        },
        indent=2,
    ))
    output = None
    async with create_agent() as agent:
        async for event in agent.astream({"messages": str(query)}, {"configurable": {"thread_id": str(context.session_id)}}, stream_mode="updates"):
            for value in event.items():
                yield {"update": value}
            output = event
            # logger.info(json.dumps(output, indent=2))
            final_response = ""
            if 'agent' in output:
                for message in output['agent']['messages']:
                    final_response += message.content
        yield MessagePart(content=final_response)