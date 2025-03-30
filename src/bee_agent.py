import asyncio
import os
from beeai_framework.backend.chat import ChatModel
from beeai_framework.workflows.agent import AgentWorkflow, AgentWorkflowInput
from beeai_framework.tools.mcp_tools import MCPTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

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
        print("Loaded MCP tool: ", tool[0].name)
        return tool[0]

mcp_weather_tool = asyncio.run(get_mcp_tools('weather_tool'))
mcp_search_tool = asyncio.run(get_mcp_tools('search_tool'))

async def main() -> None:
    llm = ChatModel.from_name(
        f"watsonx:{os.environ['MODEL_ID']}",
        {
            "project_id": os.environ['WX_PROJECT_ID'],
            "api_key": os.environ['WATSONX_APIKEY'],
            "api_base": os.environ['WATSONX_URL']
        },
    )

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