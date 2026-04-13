## 🔐 Laboratory Work: LLM Workflow Defense and Query Rewriting

This laboratory work introduces students to the concept of **LLM workflows** and demonstrates that the final output presented to a user may be the result of **multiple coordinated agents**, not a single LLM response.

The lab focuses on **defensive processing of user input** and shows how user queries can be:

* checked,
* rewritten,
* constrained,
* or sanitized

*before* being answered by an LLM or being executed by LLM-agent.

This laboratory builds directly on the previous lab devoted to **single-agent development** and introduces **multi-agent workflows** as a core architectural concept.

---

## 🎯 Learning Objectives

By completing this laboratory work, students will:

1. **Understand that user-visible output is not necessarily the direct output of an LLM**, but may be the result of a complete workflow involving multiple agents.
2. Learn how **LLM-based systems can protect themselves** by inspecting, rewriting, or restricting user input.
3. Gain hands-on experience with **multi-agent workflows** using Microsoft Agent Framework.
4. Understand the role of **intermediate agents** (policy checks, rewriting agents, guards).
5. Learn how to **document an agent workflow** as both:

   * a technical specification, and
   * an explanation of system behavior.

---

## 🧠 Key Concept

> **An LLM application is not just a prompt.
> It is a workflow.**

In real systems:

* the user’s question may never reach the answering LLM unchanged;
* intermediate agents may validate, rewrite, or reject it;
* the final response may be intentionally constrained for safety.

This laboratory demonstrates this principle explicitly.

---

## 🧩 Workflow Overview

The provided example workflow follows this structure:

```
User Query
   ↓
Intent / Policy Agent
   ↓ (allowed)
Rewrite Agent
   ↓
Answering Agent
```

If the query is **not allowed**, the workflow returns a refusal instead of an answer.

This structure illustrates a **defensive LLM pipeline**, similar to input validation and sanitization in classical software systems.

---

## 🛠 Provided Environment

The laboratory uses the same Docker-based environment as the previous lab and includes:

* Microsoft Agent Framework
* A Developer UI (Dev UI)
* Example agents and workflows

No local model deployment is required.

Students must configure access to an external LLM service (e.g., Groq, OpenAI, etc.) via environment variables.

---

## 📌 Student Task

Your task is to **design and document a defensive LLM workflow** that makes a user query *less dangerous* while preserving its usefulness.

### Core Task

You must implement a workflow in which:

1. A user submits an **unsafe or potentially dangerous query**.
2. An intermediate agent **rewrites the query** to make it safer.
3. The rewritten query is then passed to an answering agent.
4. The user only sees the **final safe response**.

The rewritten query must:

* preserve the **original intent**,
* remove or neutralize **dangerous phrasing**,
* remain useful and meaningful.

---

## 📂 Implementation Requirements

* Your workflow must use **at least two agents**.
* One agent **must perform query rewriting**.
* The workflow must demonstrate **sequential processing** (not only routing).
* The rewritten query must be clearly visible in logs or example output.

---

## 📄 Required Deliverables

Each student (or group) must submit:

### 1. Workflow Implementation

* A Python implementation of the workflow.
* Clear agent definitions and system prompts.

### 2. `README.md` for the Workflow (Required)

You must include a `README.md` describing:

1. **Workflow Purpose**
   What problem does this workflow solve?

2. **Agents Description**
   What does each agent do?

3. **Security Rationale**
   Why is rewriting needed? What risk does it reduce?

4. **Example Interaction**
   A step-by-step example showing:

   * original user query,
   * rewritten query,
   * final response.

---

## 🧪 Example Task Statement 

> “Rewrite a potentially dangerous user query so that it remains useful but does not violate safety constraints or security expectations.”

---

## 📝 Evaluation Criteria

Submissions will be evaluated based on:

1. Correct use of a **multi-agent workflow**
2. Clear and justified **rewriting logic**
3. Technical correctness of the implementation
4. Quality and clarity of the workflow README
5. Demonstrated understanding of **defensive LLM design**

---

## 📎 Notes

* This lab is **conceptual and architectural**, not model-training focused.
* Simplicity and clarity are preferred over complex logic.
* The goal is to understand **how LLM systems are structured**, not to defeat safety mechanisms.

---

## 📚 References

* [*Microsoft Agent Framework documentation*](https://learn.microsoft.com/en-us/agent-framework/tutorials/overview)
* Previous laboratory: [*Introduction to LLM Agents and Tool Usage*](../lab4/README.md)
* Workflow example for this lab: [*LLM-agent Defensive Workflow Example*](app/llm_defense)

---

