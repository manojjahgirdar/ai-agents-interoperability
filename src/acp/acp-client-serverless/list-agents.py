from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart
import asyncio

# Replace the base_url with your ACP server url
base_url = "http://ec2-54-197-70-0.compute-1.amazonaws.com:8000"

async def list_agents():
    global base_url
    client = Client(base_url=base_url)
    agents_list = {"agents": []}
    async for agent in client.agents():
        agents_list["agents"].append({
            "name": agent.name,
            "description": agent.description,
        })
    return agents_list

def lambda_handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(list_agents())