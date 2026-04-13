import os

import chainlit as cl
from autogen import ConversableAgent

# ---------------------------
#  LLM configuration
# ---------------------------

api_base_url = os.getenv("API_BASE_URL")
api_key = os.getenv("API_KEY")
model = os.getenv("MODEL", "qwen/qwen3-32b")

if not api_key:
    raise RuntimeError(
        "API_KEY is not set. "
        "Set it in your .env file or docker compose environment."
    )

llm_config = {
    "config_list": [
        {
            "model": model,
            "api_key": api_key,
            "base_url": api_base_url,
        }
    ],
}

# ---------------------------
#  System prompt
# ---------------------------

SYSTEM_PROMPT = """
You're a friendly agent.
Ask the user for their name and greet them personally.
"""

# ---------------------------
#  Chainlit event handlers
# ---------------------------

@cl.on_chat_start
async def on_chat_start():
    """Create a fresh AG2 assistant for each new conversation."""
    assistant = ConversableAgent(
        name="hello_world_agent",
        system_message=SYSTEM_PROMPT,
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    cl.user_session.set("assistant", assistant)


@cl.on_message
async def on_message(message: cl.Message):
    """Handle each incoming user message using AG2 async single-agent execution."""
    assistant: ConversableAgent = cl.user_session.get("assistant")

    response = await assistant.a_run(
        message=message.content,
        clear_history=False,
        max_turns=4,
        summary_method="last_msg",
        user_input=False,
    )

    async for _ in response.events:
        pass

    summary = await response.summary
    reply_text = str(summary or "")
    await cl.Message(content=reply_text).send()
