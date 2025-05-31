# AI Agents Interoperability Series
Learn how to architect Agentic AI solutions which are framework agnostic, LLM Agnostic. Refer to the Blog series below to learn more:

## Reference Architecture

![image](https://github.com/user-attachments/assets/15f1d121-77d3-4937-a394-9ee9c87af1a8)

## Instructions

Instructions to setup the Agents Interoperability can be found here: [Instructions to setup](https://medium.com/@manojjahgirdar/list/ai-agents-interoperability-607c343d3b1c)

## Setup codebase

1. Clone the repo.
   ```bash
   git clone https://github.com/manojjahgirdar/ai-agents-interoperability.git
   ```
   > Note: UV Package manager is recommended.
   
1. Install the uv package manager.
   ```bash
   pip install pipx
   pipx install uv
   ```
   
1. Once the uv package manager is installed, create a virtual environment and activate it.
   ```bash
   uv venv
   source .venv/bin/activate
   ```
   
1. Install the python dependencies.
   ```bash
   uv sync
   ```
   
 1. Export env variables
    ```bash
    cp env.example .env
    ```
    >Fill the env values

1. Launch the mcp/acp servers.
   1. To launch the mcp server run:
      ```bash
      cd src/mcp/mcp-server
      uv run mcp_server.py
      ```
   1. To launch the acp server, in another terminal run:
      ```bash
      cd src/acp/acp-server
      uv run acp_server.py
      ```
