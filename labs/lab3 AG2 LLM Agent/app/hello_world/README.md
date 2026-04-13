# hello-world-agent

## 1. Agent Name

**hello-world-agent**

---

## 2. Agent Purpose

The purpose of this agent is to demonstrate the **minimal setup and structure of an LLM agent** using the AG2 framework with a Chainlit user interface.

This agent is designed to:
- interact with the user in a simple conversational flow,
- request the user's name,
- greet the user personally using the provided name.

This description serves as a **technical specification for the agent's system prompt**.  
The agent does not perform analysis and does not solve a cybersecurity task.

> **Note:**  
> This agent is provided as a *demonstration example*.  
> It does **not** satisfy the laboratory requirement for tool usage and therefore **cannot be submitted as a lab solution**.

---

## 3. Agent Tools

This agent **does not use any tools**.

- No functions are registered with the agent.
- All behavior is implemented via the system prompt and conversational logic.

> **Important:**  
> In the actual laboratory assignment, students must implement agents that **use at least one tool**.  
> This agent intentionally omits tools to keep the example minimal and focused on agent structure.

---

## 4. Implementation Details

This agent uses:
- **AG2** `ConversableAgent` with an OpenAI-compatible LLM backend,
- **Chainlit** for the chat UI,
- `generate_reply()` to produce responses based on the maintained conversation history.

Each new conversation creates a fresh agent instance and message history stored in the Chainlit user session.

---

## 5. Example Interaction

```
User: Hi! Who are you?
Agent: Hello! 👋 I'm here to help you out. What's your name?

User: I'm Slava
Agent: Nice to meet you, Slava! 👋 How can I help you today?
```

---

## Additional Notes

- This agent demonstrates:
  - basic AG2 agent initialization,
  - system prompt definition,
  - interaction with an external LLM service via OpenAI-compatible API,
  - Chainlit integration for a web-based chat UI.
- It is intended as a **starting point** for understanding how agents are defined and run.
- More advanced examples build upon this structure by adding **tools and function calling**.
