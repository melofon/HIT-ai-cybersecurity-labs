import os

from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient

base_url = os.getenv("API_BASE_URL", "https://openrouter.ai/api/v1")
api_key = os.getenv("API_KEY")
model_id = os.getenv("MODEL", "x-ai/grok-4.1-fast:free")

client = OpenAIChatClient(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    model_id="x-ai/grok-4.1-fast:free",
)

agent = ChatAgent(
    chat_client=client,
    name="hello-world-agent",
    instructions="""
        You're a friendly agent.
        Ask the user for their name and greet them personally.
    """
)
