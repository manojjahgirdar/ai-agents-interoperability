from langchain_openai import ChatOpenAI

from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient

from langgraph.prebuilt import create_react_agent

import asyncio
import os

if os.getenv('OPENAI_API_KEY'):
    llm = ChatOpenAI(model="o3-mini")
else:
    print('Export OPENAI_API_KEY to initialize OpenAI LLM.')
    exit(1)

@asynccontextmanager
async def main():
    async with MultiServerMCPClient(
        {
            "mcp_server": {
                "url": "https://manojs-mcp-server.xyz.codeengine.appdomain.cloud/sse", # Replace with your Remote MCP Server URL
                "transport": "sse"
            }
        }
    ) as client:
        agent = create_react_agent(
                llm,
                tools=client.get_tools(),
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
