# Lab 3: LLM Agents and Tool Usage

Welcome to the Chainlit interface for Laboratory Work 3.

Use this chat to interact with the reference AG2 agent and inspect how it responds to user messages.

What to pay attention to:

- The agent is not only generating text. It may call Python functions exposed as tools.
- Tool calls are displayed in the UI as expandable steps.
- The reference agent is implemented in `app/agent/app.py`.

Suggested first prompts:

- `What datasets are available?`
- `Describe the orders dataset.`
- `Show the full content of the customers dataset.`

For your submission, replace or extend the reference agent under `app/agent/`, and document your work in `app/agent/README.md`.

This page is loaded from `chainlit.md`. In this course, it is used as the student-facing welcome screen inside the Chainlit UI.
