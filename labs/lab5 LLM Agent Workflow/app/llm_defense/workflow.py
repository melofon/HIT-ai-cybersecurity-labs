import os

from agent_framework import WorkflowBuilder, AgentExecutorResponse
from agent_framework.openai import OpenAIChatClient
from pydantic import BaseModel, Field

# from agent_framework import InMemoryCheckpointStorage

# checkpoint_storage = InMemoryCheckpointStorage()

base_url = os.getenv("API_BASE_URL")
api_key = os.getenv("API_KEY")
model_id = os.getenv("MODEL", "qwen/qwen3-32b")

client = OpenAIChatClient(
    base_url=base_url,
    api_key=api_key,
    model_id=model_id,
)

class QuestionCheckResult(BaseModel):
    intent: str = Field(description="One of: greeting, goodbye, weather, geography, other")

question_check_agent = client.create_agent(
    name="question-check-agent",
    description="Classifies whether a user message can be answered",
    instructions="""
        You are NOT a conversational agent.

        Classify the user's message into exactly one intent:
        - greeting
        - goodbye
        - weather
        - geography
        - other

        Return JSON in this exact format:
        {
            "intent": "one of: greeting, goodbye, weather, geography, other"
        }

        Return ONLY valid JSON. No explanations, no markdown, no code blocks.
    """,
    output_model=QuestionCheckResult,
)

geography_weather_agent = client.create_agent(
    name="geography-weather-agent",
    instructions="""
        You're a geography and weather assistant.
    """
)

refusal_agent = client.create_agent(
    name="refusal-agent",
    instructions="""
        You politely refuse to answer.

        Explain that you are a geography and weather assistant
        and cannot answer questions outside your allowed topics.

        Keep the answer short and polite.
    """,
)

# Workflow definition
def is_allowed(expected_result: bool):

    def condition(message: AgentExecutorResponse) -> bool:
        is_eligible =  (
            True if
                QuestionCheckResult.model_validate_json(message.agent_run_response.text).intent
                in ("greeting", "goodbye", "weather", "geography")
            else False )
        return is_eligible == expected_result 

    return condition

#question_check_executor = AgentExecutor(question_check_agent, id="question_check_agent")
#geography_weather_executor = AgentExecutor(geography_weather_agent, id="geography_weather_agent")
#refusal_executor = AgentExecutor(refusal_agent, id="refusal_agent")

workflow = (
    WorkflowBuilder()
    .set_start_executor(question_check_agent)
    .add_edge(question_check_agent, geography_weather_agent, is_allowed(True))
    .add_edge(question_check_agent, refusal_agent, is_allowed(False))
    .build()
)

class WorkflowWrapper:
    def __init__(self, wf):
        self._workflow = wf
    
    async def run_stream(self, input_data=None, checkpoint_id=None, checkpoint_storage=None, **kwargs):
        """
        Wrapper to eliminate devUI error with checkpoint parameters
        """
        # If checkpoint_id defined - it's continuation, not yet supported
        if checkpoint_id is not None:
            raise NotImplementedError("Checkpoint resume is not yet supported")
        
        async for event in self._workflow.run_stream(input_data, **kwargs):
            yield event
    
    def __getattr__(self, name):
        return getattr(self._workflow, name)

workflow = WorkflowWrapper(workflow)