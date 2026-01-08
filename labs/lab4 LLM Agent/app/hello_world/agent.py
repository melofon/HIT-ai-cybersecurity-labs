import os

from agent_framework.openai import OpenAIChatClient

base_url = os.getenv("API_BASE_URL")
api_key = os.getenv("API_KEY")
model_id = os.getenv("MODEL", "qwen/qwen3-32b")

client = OpenAIChatClient(
    base_url=base_url,
    api_key=api_key,
    model_id=model_id,
)

agent = client.create_agent(
    name="Hello World Agent",
    instructions="""
        You're a friendly agent.
        Ask the user for their name and greet them personally.
    """
)
