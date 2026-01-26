import os
from typing import Literal
from deepagents import create_deep_agent
from tavily import TavilyClient

# Initialize Tavily client
tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# ---------------------------------------------------------------
# TOOL 1: Internet Search (using Tavily)
# ---------------------------------------------------------------
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "finance",
    include_raw_content: bool = False,
):
    """Search the web for financial or market-related information"""
    search_docs = tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )
    return search_docs


# ---------------------------------------------------------------
# TOOL 2: Market Data Tool (Mock Example)
# ---------------------------------------------------------------
def market_data_tool(
    symbol: str = "^NSEI",
    range_days: int = 7,
):
    """Fetch latest market data for a given symbol (Mock). 
    You can integrate Alpha Vantage, Yahoo Finance, or any API later."""
    mock_data = {
        "symbol": symbol,
        "range_days": range_days,
        "data": [
            {"date": "2025-11-05", "price": 22450.5},
            {"date": "2025-11-06", "price": 22520.3},
            {"date": "2025-11-07", "price": 22710.8},
            {"date": "2025-11-08", "price": 22685.2},
            {"date": "2025-11-11", "price": 22815.9},
        ],
        "summary": "Nifty 50 index rose 1.6% over the last 5 days amid strong earnings and global cues.",
    }
    return mock_data


# ---------------------------------------------------------------
# TOOL 3: News Sentiment Tool (Mock Example)
# ---------------------------------------------------------------
def news_sentiment_tool(news_headlines: list[str]):
    """Analyze sentiment of financial news headlines (Mock).
    You can replace with a real sentiment model."""
    positive_keywords = ["gain", "growth", "up", "beat", "strong"]
    negative_keywords = ["loss", "down", "decline", "fall", "weak"]

    score = 0
    for headline in news_headlines:
        if any(word in headline.lower() for word in positive_keywords):
            score += 1
        elif any(word in headline.lower() for word in negative_keywords):
            score -= 1

    sentiment = "Neutral"
    if score > 1:
        sentiment = "Positive"
    elif score < -1:
        sentiment = "Negative"

    return {
        "sentiment_score": score,
        "sentiment_label": sentiment,
        "summary": f"Overall market sentiment appears {sentiment.lower()} based on recent news tone.",
    }


# ---------------------------------------------------------------
# SYSTEM PROMPT: Financial Market Summary Agent
# ---------------------------------------------------------------
financial_market_prompt = """
You are a Financial Market Research Assistant.

Your job is to provide a clear and detailed summary of current market trends,
combining data, sentiment, and news analysis.

Follow these steps:
1. Use market_data_tool to retrieve the latest market data for relevant indices or stocks.
2. Use internet_search (topic="finance") to find recent financial news headlines.
3. Use news_sentiment_tool to assess whether the market sentiment is bullish, bearish, or neutral.
4. Combine these findings into a cohesive market summary.

The final report should include:
- **Market Overview** - performance of major indices or assets
- **Recent Drivers** - key events influencing movements
- **Market Sentiment** - from recent headlines or news tone
- **Conclusion** - summary of market outlook or trends

Format your response as Markdown:
# Market Summary
## Market Overview
## Recent Drivers
## Market Sentiment
## Conclusion

Keep tone professional and concise.
Include data and clear observations.
"""


# ---------------------------------------------------------------
# CREATE THE AGENT
# ---------------------------------------------------------------
agent = create_deep_agent(
    model="ollama:gpt-oss:20b",
    tools=[internet_search, market_data_tool, news_sentiment_tool],
    instructions=financial_market_prompt
)

# ---------------------------------------------------------------
# Example Usage
# ---------------------------------------------------------------
if __name__ == "__main__":
    question = "Summarize the latest trends in the Indian stock market"
    response = agent.run(question)
    print(response)