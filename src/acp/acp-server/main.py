import asyncio
from collections.abc import AsyncGenerator
from acp_sdk.models.models import MessagePart
from acp_sdk.models import Message
from acp_sdk.server import Context, RunYield, RunYieldResume, Server

server = Server()

from src.agents import *

if __name__ == "__main__":
    # Run the server
    print("Starting ACP server...")
    server.run(host="0.0.0.0", port=8081)