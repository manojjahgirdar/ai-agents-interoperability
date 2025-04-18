from ibm_watsonx_ai.metanames import GenTextParamsMetaNames
from langchain_ibm import ChatWatsonx
from langchain_openai import ChatOpenAI

from contextlib import asynccontextmanager
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import os

if os.getenv('OPENAI_API_KEY'):
    llm = ChatOpenAI(model="o3-mini")
elif os.getenv('WATSONX_APIKEY'):
    llm = ChatWatsonx(
        model_id=os.environ['MODEL_ID'],
        url=os.environ['WATSONX_URL'],
        project_id=os.environ['WX_PROJECT_ID'],
        params={
            GenTextParamsMetaNames.MAX_NEW_TOKENS: 250,
            GenTextParamsMetaNames.MIN_NEW_TOKENS: 20,
            GenTextParamsMetaNames.DECODING_METHOD: 'greedy',
            
        },
    )
else:
    print('Export OPENAI_API_KEY or WATSONX_APIKEY to initialize OpenAI or Watsonx LLM.')
    exit(1)
    

server_params = StdioServerParameters(
    command="python",
    args=["mcp_server.py"],
)

@asynccontextmanager
async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Get tools
            tools = await load_mcp_tools(session)
            for tool in tools:
                print(f"Loaded MCP tool: {tool.name}")
            #     print(f"Description: {tool.description}")

            # Create and run the agent
            agent = create_react_agent(
                llm,
                tools=tools,
                prompt="You are a helpfull assistant."
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


