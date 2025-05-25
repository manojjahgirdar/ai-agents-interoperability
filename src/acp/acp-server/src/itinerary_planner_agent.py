import json
from main import Context, RunYield, RunYieldResume, server, Message, MessagePart
from functools import reduce
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableLambda
from langgraph.graph import StateGraph
from src.tools import LangChainTOOLS
import asyncio
import os
from collections.abc import AsyncGenerator

# Define LLM
llm = ChatOpenAI(model="o3-mini")

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

# Define the graph
agent = create_react_agent(
    llm,
    tools=LangChainTOOLS,
    checkpointer=memory,
    state_modifier=system_prompt
)

@server.agent()
async def itinerary_provider_agent(inputs: list[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """An itinerary provider agent that uses the LangChain framework to gather information about tourist attractions and weather details for a given city using the web search tool and weather tool."""
    query = reduce(lambda x, y: x + y, inputs)
    print(json.dumps(
        {
            "session_id": str(context.session_id),
            "prompt": str(query)
        },
        indent=2,
    ))
    output = None
    async for event in agent.astream({"messages": str(query)}, {"configurable": {"thread_id": str(context.session_id)}}, stream_mode="updates"):
        for value in event.items():
            yield {"update": value}
        output = event
        # print(json.dumps(output, indent=2))
        final_response = ""
        if 'agent' in output:
            for message in output['agent']['messages']:
                final_response += message.content
    yield MessagePart(content=final_response)
