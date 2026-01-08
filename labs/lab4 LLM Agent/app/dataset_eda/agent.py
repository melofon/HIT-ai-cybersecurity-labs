import os
from typing import Annotated, Dict

from agent_framework import ChatAgent, ai_function
from agent_framework.openai import OpenAIChatClient
from pydantic import Field

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
#  Tools
# ---------------------------

@ai_function(
    name="list_datasets",
    description="Return all available datasets with basic information about them.",
)
def list_datasets() -> Dict:
    """
    List all datasets with the number of records and fields for each.
    """
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


@ai_function(
    name="describe_dataset",
    description=(
        "Describe a single dataset: how many records it has, how many fields, "
        "and what these fields are."
    ),
)
def describe_dataset(
    dataset_name: Annotated[
        str,
        Field(
            description=(
                "Name of the dataset to describe. "
                "Must be one of: 'customers', 'orders'."
            )
        ),
    ],
) -> Dict:
    """
    Return detailed information for a specific dataset.
    """
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


@ai_function(
    name="show_data",
    description=(
        "Returns a single dataset raw data"
    ),
)
def raw_data(
    dataset_name: Annotated[
        str,
        Field(
            description=(
                "Name of the dataset to extract. "
                "Must be one of: 'customers', 'orders'."
            )
        ),
    ],
) -> Dict:
    """
    Return raw data for a specific dataset.
    """
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
#  Provider config
# ---------------------------

base_url = os.getenv("API_BASE_URL")
api_key = os.getenv("API_KEY")
model_id = os.getenv("MODEL", "qwen/qwen3-32b")

if not api_key:
    raise RuntimeError(
        "API_KEY is not set. "
        "Set it in your .env file or docker compose environment."
    )

client = OpenAIChatClient(
    base_url=base_url,
    api_key=api_key,
    model_id=model_id,
)

# ---------------------------
#  Agent definition for DevUI
# ---------------------------

agent = client.create_agent(
    name="Dataset EDA Agent",
    instructions="""
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

        Rules:
        1) If the user asks what datasets are available or wants an overview,
           always call list_datasets.
        2) If the user asks about a specific dataset (how many records it has,
           how many fields, what the columns are), call describe_dataset for
           that dataset.
        3) If the user asks general questions about data analysis (e.g. how to
           interpret the fields or what analysis could be done), first use the
           tools to understand the structure of the data, and then answer in
           natural language based on the tool results.
        4) For casual small talk (hello, how are you), answer briefly
           (e.g. 'Hi', 'All good', 'Okay'), but if the question is about the
           datasets, focus on using the tools.
        
        Always answer in English.
    """,
    tools=[
        list_datasets,
        describe_dataset,
        raw_data,
    ],
)
