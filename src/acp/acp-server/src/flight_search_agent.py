import asyncio
import json
import os
from functools import reduce
from main import Context, RunYield, RunYieldResume, server, Message, MessagePart
from collections.abc import AsyncGenerator
from beeai_framework.emitter import Emitter, EventMeta, EmitterOptions
from beeai_framework.workflows.agent import AgentWorkflow, AgentWorkflowInput
from beeai_framework.errors import FrameworkError
from beeai_framework.agents.react.agent import ReActAgent
from beeai_framework.adapters.openai import OpenAIChatModel
from beeai_framework.memory.token_memory import TokenMemory
from beeai_framework.backend.message import (
        UserMessage,
        SystemMessage,
    )

from src.tools import BeeAITools

from src.core.llm_provider import LLMProvider

def process_agent_events(data, event: EventMeta) -> None:
    """Process agent events and log appropriately"""

    if event.name == "error":
        print("Agent 🤖 : ", FrameworkError.ensure(data.error).explain())
    elif event.name == "retry":
        print("Agent 🤖 : ", "retrying the action...")
    elif event.name == "update":
        print(f"Agent({data.update.key}) 🤖 : ", data.update.parsed_value)
    elif event.name == "start":
        print("Agent 🤖 : ", "starting new iteration")
    elif event.name == "success":
        print("Agent 🤖 : ", "success")
    else:
        pass

def observer(emitter: Emitter) -> None:
    emitter.on("*.*", process_agent_events)

@server.agent()
async def flight_discovery_agent(inputs: list[Message], context: Context) -> AsyncGenerator[RunYield, RunYieldResume]:
    """A Flight Discovery agent that uses the Bee AI framework to gather information about flights and airports."""
    query = reduce(lambda x, y: x + y, inputs)
    print(json.dumps(
        {
            "session_id": str(context.session_id),
            "prompt": str(query)
        },
        indent=2,
    ))
    # Create a llm instance
    llm = OpenAIChatModel(
            model="gpt-3.5-turbo",
            api_key=os.getenv("OPENAI_API_KEY"),
            api_base="https://api.openai.com/v1",
        )
    
    # Create a memory instance
    memory = TokenMemory(llm)

    # Add system message to memory
    system_message = SystemMessage(
        content="You are a flight discovery agent. Use the tools to get flight and airport details. Respond in a structured markdown format.",
    )
    await memory.add(system_message)

    user_message = UserMessage(
        content=str(query)
    )

    # Add messages to memory
    await memory.add(user_message)
        
    # Create agent with memory and tools
    agent = ReActAgent(llm=llm, tools=BeeAITools, memory=memory)

    # Run the agent with the memory
    # response = await agent.run().on("*", process_agent_events, EmitterOptions(match_nested=False))
    response = await agent.run()
    
    # Yield the response
    yield MessagePart(content=response.result.content[0].text)
