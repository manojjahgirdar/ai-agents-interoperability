import os

# Add all the env variables here
class AppConfig:
    MCP_AUTH_TOKEN: str = os.getenv("MCP_AUTH_TOKEN")