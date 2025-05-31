from acp_sdk.client import Client
from acp_sdk.models import Message, MessagePart
import asyncio

# Replace the base_url with your ACP server URL
base_url = "http://ec2-54-197-70-0.compute-1.amazonaws.com:8000"

async def invoke_agent(agent_name: str, prompt: str):
    global base_url
    client = Client(base_url=base_url) 
    run = await client.run_sync(
        agent=agent_name,
        input=[
            Message(
                parts=[MessagePart(content=prompt, content_type="text/plain")]
            )
        ],
    )
    return run.output[0].parts[0].content

def lambda_handler(event, context):
    agent_name = event.get("agent_name")
    prompt = event.get("prompt")
    
    if not agent_name or not prompt:
        return {
            "statusCode": 400,
            "body": "Missing 'agent_name' or 'prompt' in the request."
        }

    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(invoke_agent(agent_name, prompt))
    return {
        "statusCode": 200,
        "body": str(response)
    }