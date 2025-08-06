import dotenv

dotenv.load_dotenv()

from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver

# Define LLM
llm = ChatOllama(model="gpt-oss:20b")

# Define tool
search_tool = TavilySearch(
    max_results=5,
   topic="general"
)

# Define agent
agent = create_react_agent(
    model=llm,
    tools=[search_tool],
    checkpointer=MemorySaver()
)

prompts = ["Who is Manoj Jahgirdar?", "What are his hobbies?"]

config = {"configurable": {"thread_id": "1", "recursion_limit": 150}}

for prompt in prompts:
    events = agent.stream(
        {"messages": [("user", prompt)]},
        config,
        stream_mode="values",
    )

    for event in events:
        event["messages"][-1].pretty_print()
