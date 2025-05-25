import asyncio
import os
from beeai_framework.backend.chat import ChatModel
from beeai_framework.adapters.openai import OpenAIChatModel
from beeai_framework.workflows.agent import AgentWorkflow, AgentWorkflowInput
from beeai_framework.tools.mcp_tools import MCPTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import logging

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'ERROR'))
logger = logging.getLogger(__name__)

server_params = StdioServerParameters(
    command="python",
    args=["mcp_server.py"],
)

async def get_mcp_tools(name) -> MCPTool:
    async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        # Discover tools through MCP client
        tools = await MCPTool.from_client(session)
        filter_tool = filter(lambda tool: tool.name == name, tools)
        tool = list(filter_tool)
        logger.info("Loaded MCP tool: ", tool[0].name)
        return tool[0]

mcp_weather_tool = asyncio.run(get_mcp_tools('weather_tool'))
mcp_search_tool = asyncio.run(get_mcp_tools('search_tool'))

def _get_openai(model="gpt-3.5-turbo"):
    return OpenAIChatModel(
        model=model,
        api_key=os.getenv("OPENAI_API_KEY"),
        api_base="https://api.openai.com/v1",
    )

async def main() -> None:
    llm = _get_openai()

    workflow = AgentWorkflow(name="Smart assistant")

    workflow.add_agent(
        name="WeatherForecaster",
        role="A weather reporter.",
        instructions="You provide detailed weather reports.",
        tools=[mcp_weather_tool],
        llm=llm,
    )

    location = "Bengaluru"

    response = await workflow.run(
        inputs=[
            AgentWorkflowInput(
                prompt=f"Provide a comprehensive weather summary for {location} today.",
                expected_output="Essential weather details such as temperature. Only report information that is available.",
            ),
        ]
    ).on(
        "success",
        lambda data, event: print(
            f"\n-> Step '{data.step}' has been completed with the following outcome.\n\n{data.state.final_answer}"
        ),
    )

    print("==== Final Answer ====")
    print(response.result.final_answer)


if __name__ == "__main__":
    asyncio.run(main())
