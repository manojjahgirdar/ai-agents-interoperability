# Build AI Agent with OpenAI's Open-source 20B model on device

Read more here in my [blog post](https://medium.com/@manojjahgirdar/build-ai-agents-with-gpts-20b-oss-model-on-your-local-machine-114c86e76eba).

## Setup and run

>Note: `uv` package manager is recommended.

1. (Optional) Create a virtual environment.
   ```bash
   uv venv
   source .venv/bin/activate
   ```

1. Install the python dependencies.
   ```bash
   uv sync --frozen
   ```

1. Export the `TAVILY_API_KEY` fot the tavily search tool.
   ```bash
   export TAVILY_API_KEY="YOUR_API_KEY"
   ```

 1. Run the LangGraph agent.
    ```bash
    uv run agent.py
    ```

