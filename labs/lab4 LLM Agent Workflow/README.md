# Lab 4: Defensive and Adversarial LLM Agent Workflows

This laboratory work is part of the **AI-Enhanced Cybersecurity** course. It
introduces students to the design of LLM-agent workflows in which the final
response is produced by a controlled process, not by a single direct LLM call.

The main goal of this lab is **architectural design**: students must learn how to
design defensive and adversarial agent workflows, define agent responsibilities,
and explain how workflow logic controls unsafe or unauthorized behavior.

This lab is fully containerized. Students run the application with **Docker** and
**Docker Compose**.

---

## 1. Key Concept

> An LLM application is not just a prompt. It is a workflow.

In real cybersecurity systems:

* user input may be inspected before it reaches an answering agent,
* intermediate agents may classify, rewrite, reject, or constrain a request,
* attacker-style agents may test whether a workflow can be bypassed,
* defender-style agents may enforce policy or reduce risk,
* the user-visible response may be the result of several coordinated decisions.

This laboratory demonstrates this principle through a defensive workflow where a
policy agent protects a domain-specific answering agent.

---

## 2. Learning Objectives

By completing this lab, students will:

1. Understand the role of workflow design in LLM-based cybersecurity systems.
2. Learn how defender agents can protect a main LLM agent from unauthorized use.
3. Learn how attacker-style scenarios can be used to test workflow weaknesses.
4. Practice separating agent responsibilities: policy, answering, refusal, audit,
   rewriting, or adversarial testing.
5. Document an agent workflow as a technical security design, not only as code.

---

## 3. Provided Example

The provided example is a small defensive workflow implemented with **AG2** and
served through **Chainlit**.

```text
User Query
   |
   v
QuestionCheckAgent
   |--------------------|
   | allowed            | not allowed
   v                    v
GeographyWeatherAgent   RefusalAgent
```

The example shows the following pattern:

1. The user submits a query.
2. `QuestionCheckAgent` classifies the query intent.
3. Allowed intents are routed to `GeographyWeatherAgent`.
4. Unauthorized intents are routed to `RefusalAgent`.
5. Chainlit shows the policy decision and final answer.

The example allowed intents are:

```text
greeting, goodbye, weather, geography
```

All other intents are treated as unauthorized.

This example is intentionally simple. Its purpose is to show the workflow pattern,
not to provide a complete security product.

---

## 4. Student Task

Your task is to **design, implement, and document an LLM-agent workflow for a
cybersecurity-relevant scenario**.

The workflow may be defensive, adversarial, or a combination of both. The important
requirement is that the application must be designed as a workflow of agents with
clear responsibilities and explicit control logic.

Acceptable workflow directions include:

* **Defensive policy gate** - inspect a user query and decide whether it may reach
  the main agent.
* **Query rewriting** - rewrite unsafe or overly broad requests into safer,
  constrained requests before answering.
* **Attacker / defender workflow** - use one agent to generate adversarial prompts
  and another agent to evaluate or block them.
* **Evaluator workflow** - route a generated answer through a review agent before
  showing it to the user.
* **Domain restriction workflow** - allow only a specific cybersecurity task or
  knowledge domain and refuse everything else.

The workflow should demonstrate that the final response is controlled by system
logic, not just by one model prompt.

---

## 5. Design Requirements

Your workflow must satisfy the following requirements:

1. Use at least two agents or workflow components.
2. Include at least one intermediate decision point before the final response.
3. Clearly separate responsibilities between agents.
4. Demonstrate either defensive behavior, adversarial testing, or both.
5. Prevent unauthorized or out-of-scope requests from directly reaching the
   protected answering agent.
6. Show enough intermediate information in Chainlit to understand the workflow
   behavior.

Keep the design simple. A well-explained two-agent workflow is better than a large
unclear system.

---

## 6. Required Documentation

Your updated README must describe:

1. **Workflow Purpose** - what security problem or scenario the workflow addresses.
2. **Agents Description** - what each agent is responsible for.
3. **Workflow Logic** - how requests move between agents.
4. **Security Rationale** - why the workflow reduces risk or tests a weakness.
5. **Example Interaction** - a step-by-step example showing the user input,
   intermediate decision, and final response.

Do not rely on code comments as the primary explanation of your design.

---

## 7. Provided Environment

The lab uses a Docker-based environment with:

* **AG2** - LLM agent framework.
* **Chainlit** - browser-based chat UI.
* An external OpenAI-compatible LLM service.

By default, `compose.yml` is configured for the Groq OpenAI-compatible endpoint,
but students may use another compatible provider.

Repository structure:

```text
lab4 LLM Agent Workflow/
├── Dockerfile
├── compose.yml
├── pyproject.toml
├── README.md
└── app/
    └── app.py
```

The reference implementation is in `app/app.py`.

---

## 8. Build and Run

From the laboratory directory:

```bash
cd "labs/lab4 LLM Agent Workflow"
```

Create a `.env` file with your LLM API key:

```text
API_KEY=xxx_XXXXXXXXX
```

Build the Docker image:

```bash
docker build -t cybersec-agent-workflow-lab4 .
```

Run the application:

```bash
docker compose up
```

Open Chainlit in the browser:

```text
http://localhost:8000
```

Stop the application:

```bash
docker compose down
```

After changing Python code, restart Compose:

```bash
docker compose down
docker compose up
```

If you change `compose.yml`, recreate the container:

```bash
docker compose up -d --force-recreate
```

---

## 9. Evaluation Criteria

Submissions will be evaluated based on:

1. Clear workflow architecture.
1. Correct use of multiple agents or workflow components.
1. Clear separation of agent responsibilities.
1. Security relevance of the workflow design.
1. Quality of the README explanation.
1. Demonstrated understanding of defensive or adversarial LLM workflow design.
1. Correct Docker Compose and application execution.

---

## 10. References

* [AG2 documentation](https://docs.ag2.ai/)
* [Chainlit documentation](https://docs.chainlit.io/)
* [AG2 GitHub repository](https://github.com/ag2ai/ag2)
* [Chainlit GitHub repository](https://github.com/Chainlit/chainlit)

---

All user interfaces and documentation in this repository must be in English.
