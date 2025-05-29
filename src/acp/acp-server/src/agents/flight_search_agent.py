import datetime
import json
import logging
import os
from functools import reduce
from main import Context, RunYield, RunYieldResume, server, Message, MessagePart
from collections.abc import AsyncGenerator
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import SseServerParams, mcp_server_tools
from contextlib import asynccontextmanager

# Set up logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'ERROR'))
logger = logging.getLogger(__name__)

model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
)

def today_date() -> str:
    """Returns today's date in YYYY-MM-DD format."""
    return datetime.datetime.now().strftime("%Y-%m-%d")

system_prompt = """You are a flight discovery agent. Use the tools to get flight details. 
Instructions: 
1. Use the IATA code to get details and not the city name. 
2. Today's date is {date}
3. Search for flights for next day by default unless specified otherwise.
4. Search for flights for 1 passanger by default unless specified otherwise.
5. Search for flights in USD by default unless specified otherwise.
6. Respond in a structured markdown table format. 
""".format(date=today_date())

@asynccontextmanager
async def create_agent():
    fetch_mcp_server = SseServerParams(url=os.getenv("REMOTE_MCP_URL", "http://localhost:8000/sse"))
    tools = await mcp_server_tools(fetch_mcp_server)

    # Get only required tools for flight discovery
    tools = [tool for tool in tools if tool.name == "get_flight_search_results"]
    
    logger.info("Loaded MCP tools:" + ", ".join(tool.name for tool in tools))

    agent = AssistantAgent(
        name="flight_discovery_agent",
        model_client=model_client,
        tools=tools,
        system_message=system_prompt,
        reflect_on_tool_use=True,
        model_client_stream=True,  # Enable streaming tokens from the model client.
    )

    yield agent


@server.agent()
async def flight_discovery_agent(inputs: list[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """A Flight Discovery agent that uses the Microsoft Autogen framework to gather information about flights and airports."""
    query = reduce(lambda x, y: x + y, inputs)
    logger.info(json.dumps(
        {
            "session_id": str(context.session_id),
            "prompt": str(query)
        },
        indent=2,
    ))
    async with create_agent() as agent:
        response = await Console(agent.run_stream(task=str(query)))
        await model_client.close()
        yield MessagePart(content=response.messages[-1].content)
