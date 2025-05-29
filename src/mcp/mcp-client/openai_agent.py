# Note: This code is currently breaking, I am working on fixing it!

from agents import Agent, Runner, MCPServerStdio

async def main():
    async with MCPServerStdio(
        params={
            "command": "python",
            "args": ["mcp_server.py"],
        }
    ) as server:
        tools = await server.list_tools()
        return tools

async def invoke_agent(query):
    
    history_tutor_agent = Agent(
        name="History Tutor",
        handoff_description="Specialist agent for historical questions",
        instructions="You provide assistance with historical queries. Explain important events and context clearly. ",
        mcp_servers=[tools]
    )

if __name__ == "__main__":
    
    result = Runner.run_sync(agent, prompt)
    print(result.final_output)
