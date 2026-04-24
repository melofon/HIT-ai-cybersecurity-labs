import os
import json
from typing import Annotated, Dict

import chainlit as cl
from autogen import ConversableAgent
from autogen.events.agent_events import ExecuteFunctionEvent, ExecutedFunctionEvent

# ---------------------------
#  In-memory example datasets
# ---------------------------

datasets_state: Dict[str, list] = {
    "customers": [
        {"id": 1, "name": "Alice", "country": "US"},
        {"id": 2, "name": "Bob", "country": "UK"},
    ],
    "orders": [
        {"order_id": 100, "customer_id": 1, "amount": 120.5, "currency": "USD"},
        {"order_id": 101, "customer_id": 2, "amount": 99.9, "currency": "GBP"},
        {"order_id": 102, "customer_id": 1, "amount": 250.0, "currency": "USD"},
    ],
}

# ---------------------------
#  Tools (plain functions)
# ---------------------------


def list_datasets() -> Dict:
    """Return all available datasets with basic information about them."""
    datasets_info = []
    for name, rows in datasets_state.items():
        num_records = len(rows)
        num_fields = len(rows[0]) if num_records > 0 else 0
        field_names = list(rows[0].keys()) if num_records > 0 else []
        datasets_info.append(
            {
                "name": name,
                "num_records": num_records,
                "num_fields": num_fields,
                "field_names": field_names,
            }
        )
    return {"datasets": datasets_info}


def describe_dataset(
    dataset_name: Annotated[
        str,
        "Name of the dataset to describe. Must be one of: 'customers', 'orders'.",
    ],
) -> Dict:
    """Return detailed information for a specific dataset."""
    if dataset_name not in datasets_state:
        return {
            "ok": False,
            "error": "dataset_not_found",
            "message": (
                f"Dataset '{dataset_name}' not found. "
                f"Available datasets: {', '.join(datasets_state.keys())}."
            ),
        }

    rows = datasets_state[dataset_name]
    num_records = len(rows)
    num_fields = len(rows[0]) if num_records > 0 else 0
    field_names = list(rows[0].keys()) if num_records > 0 else []

    return {
        "ok": True,
        "dataset": dataset_name,
        "num_records": num_records,
        "num_fields": num_fields,
        "field_names": field_names,
        "example_row": rows[0] if num_records > 0 else None,
    }


def show_data(
    dataset_name: Annotated[
        str,
        "Name of the dataset to extract. Must be one of: 'customers', 'orders'.",
    ],
) -> Dict:
    """Return raw data for a specific dataset."""
    if dataset_name not in datasets_state:
        return {
            "ok": False,
            "error": "dataset_not_found",
            "message": (
                f"Dataset '{dataset_name}' not found. "
                f"Available datasets: {', '.join(datasets_state.keys())}."
            ),
        }

    rows = datasets_state[dataset_name]
    return {
        "ok": True,
        "dataset": dataset_name,
        "raw_data": rows,
    }


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
            "price": [0, 0],
        }
    ],
}

# ---------------------------
#  System prompt
# ---------------------------

SYSTEM_PROMPT = """\
You are a data analysis agent. You work with small tabular datasets
that are already loaded into memory and exposed via tools.

Currently you have two example datasets:
- 'customers': information about customers;
- 'orders': information about orders made by customers.

You have the following tools:
- list_datasets: show all available datasets and basic statistics
  (number of records and fields).
- describe_dataset: describe a specific dataset in more detail,
  including the number of records, the number of fields and their names.
- show_data: return the raw records of a selected dataset.

Rules:
1) If the user asks what datasets are available or wants an overview,
   always call list_datasets.
2) If the user asks about a specific dataset (how many records it has,
   how many fields, what the columns are), call describe_dataset for
   that dataset.
3) If the user asks to see the actual data or full content, call
   show_data for that dataset.
4) If the user asks general questions about data analysis (e.g. how to
   interpret the fields or what analysis could be done), first use the
   tools to understand the structure of the data, and then answer in
   natural language based on the tool results.
5) For casual small talk (hello, how are you), answer briefly
   (e.g. 'Hi', 'All good', 'Okay'), but if the question is about the
   datasets, focus on using the tools.

Always answer in English.
"""

WELCOME_MESSAGE = """\
Hello. I am the dataset analysis agent for this lab.

I can inspect the small example datasets exposed through my tools and explain
their structure in plain English. Try asking:

- What datasets are available?
- Describe the orders dataset.
- Show the full content of the customers dataset.

When I use a tool, Chainlit will show the call as an expandable step.
"""


def _format_content(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, (dict, list, tuple)):
        return json.dumps(content, ensure_ascii=True, indent=2)
    return str(content)

# ---------------------------
#  Chainlit event handlers
# ---------------------------


@cl.on_chat_start
async def on_chat_start():
    """Create the AG2 assistant and store it in the user session."""
    assistant = ConversableAgent(
        name="dataset_analysis_agent",
        system_message=SYSTEM_PROMPT,
        llm_config=llm_config,
        human_input_mode="NEVER",
        functions=[list_datasets, describe_dataset, show_data],
    )

    cl.user_session.set("assistant", assistant)
    await cl.Message(content=WELCOME_MESSAGE, author="dataset_analysis_agent").send()


@cl.on_message
async def on_message(message: cl.Message):
    """Handle each user message using AG2 async single-agent execution."""
    assistant: ConversableAgent = cl.user_session.get("assistant")

    response = await assistant.a_run(
        message=message.content,
        clear_history=False,
        max_turns=6,
        summary_method="last_msg",
        user_input=False,
    )

    tool_inputs: dict[str, dict[str, str]] = {}

    async for event in response.events:
        if isinstance(event, ExecuteFunctionEvent):
            event_data = event.content
            tool_key = getattr(event_data, "call_id", None) or event_data.func_name
            tool_inputs[tool_key] = {
                "name": event_data.func_name,
                "input": _format_content(event_data.arguments) or "(no arguments)",
            }
            continue

        if not isinstance(event, ExecutedFunctionEvent):
            continue

        event_data = event.content
        tool_key = getattr(event_data, "call_id", None) or event_data.func_name
        step_data = tool_inputs.get(
            tool_key,
            {
                "name": event_data.func_name,
                "input": "(no arguments)",
            },
        )
        async with cl.Step(name=step_data["name"], type="tool") as step:
            step.input = step_data["input"]
            step.output = _format_content(event_data.content)

    summary = await response.summary
    final_text = _format_content(summary)
    await cl.Message(content=final_text).send()
