# 🔧 **Assignment: Introduction to LLM Agents and Tool Usage**

This laboratory work is a **preparatory introduction to LLM-based agents**. Its purpose is to familiarize students with the basic concepts of agent-based systems and with practical aspects of developing and interacting with agents.

This lab serves as a prerequisite for subsequent laboratories involving **multi-agent scenarios** (for example, *attacker – evaluator – defender*). It is intentionally introductory and is **not** a standalone cybersecurity lab.

By completing this lab, students will:

* Understand what an LLM agent is and how it differs from a simple prompt-based chatbot
* Learn how agents can invoke **tools (Python functions)** as part of their operation
* Gain hands-on experience working with an agent framework in a containerized environment
* Become comfortable with the basic workflow of creating, running, and testing agents

The focus of this lab is **agent mechanics and tool integration**, not cybersecurity domain knowledge or model training.

---

## 1. Provided Environment

Agents in this laboratory are served by an external LLM inference service. By default, the provided configuration uses the **Groq** platform, but students may use any other LLM service.

Students are expected to:

* Register for a free account on an LLM service (e.g. Groq or an alternative provider)
* Create an API access key
* Provide this key to the application via environment variables

No on-premise or local model deployment is required for this lab.

This laboratory is based on a prepared Docker environment that includes:

* Microsoft Agent Framework
* A developer UI (Dev UI) for interacting with agents

The repository structure is as follows:

```
lab4/
├── Dockerfile
├── compose.yml
├── app/
│   └── app/
│       ├── hello_world/
│       ├── dataset_eda/
│       └── llm_defense/
├── .env
├── pyproject.toml
├── uv.lock
└── README.md
```

Each subdirectory inside `app/app/` represents **one independent agent**.

Several example agents are provided and can be used as references for understanding agent structure, system prompts, and tool usage.

---

## 2. Setup and Running the Environment

The environment is provided in a ready-to-use Docker configuration. No local Python setup is required.

### 2.1 Configure Environment Variables

Before building and running the application, you must configure your LLM service credentials.

1. Register with LLM service provider of your choice (e.g., Groq, OpenAI, etc.).
2. Generate an API key for accessing the LLM service. 
3. Create environment file with the name `.env` in the root of the laboratory directory.
4. Add your API key for the selected LLM service to the .env file. For example:

```
API_KEY=xxx_XXXXXXXXX
```

### 2.2 Setup an LLM Model

The LLM model used by the agents is specified in compose.yml.

Students are expected to:

* Review the list of models provided by their chosen LLM service
* Select a model that supports tool use / function calling
* Update the model name in compose.yml accordingly

LLM providers frequently release new models. Part of this lab is learning how to independently select, test and update settings for an appropriate model.

### 2.3 Build the Docker Image

From the root of the laboratory directory, build the image:

```bash
docker build -t cybersec-agent-devui .
```

### 2.4 Run the Application

Start the application using Docker Compose:

```bash
docker compose up
```

After startup, open the Dev UI in your browser (the URL is shown in the console output).

---

## 3. Student Task

You must design and implement **one simple LLM agent** to demonstrate that you understand:

* how an agent is structured,
* how a system prompt defines agent behavior,
* how tools are exposed and invoked by the agent.

Your agent does **not** need to solve a real cybersecurity problem. The task is purely educational and focuses on understanding agent concepts and mechanics.

### 3.1 Agent Location

Your agent must be implemented as a **new directory** inside:

```
app/app/
```

Example:

```
app/app/log_explainer_agent/
```

---

## 4. Mandatory Requirements

### 4.1 Tool Usage (Required)

Your agent **must use at least one tool**.

A tool is a Python function that the agent can explicitly call during interaction. The purpose of this requirement is to demonstrate the difference between:

* pure text generation, and
* agent-driven execution of functions.

The number and complexity of tools are **not important**. One simple tool is sufficient.

Agents that only generate text **without calling any tools will not be accepted**.

---

## 5. Required Deliverables

Your submission will be evaluated based on **two mandatory components** inside your agent directory:

### 5.1 `README.md` (Required)

Your agent directory must contain a `README.md` written in English with the following structure:

#### 1. Agent Name

* Any name you choose

#### 2. Agent Purpose

* A clear description of what the agent is designed to do
* This description must be written as a **technical task specification** for the agent’s system prompt

Examples:

* Explaining the structure of input data files
* Explaining the results produced by a simple analysis
* Assisting the user in interpreting program output

#### 3. Agent Tools

* A list of all tools (functions) used by the agent
* For each tool, describe:

  * what the tool does,
  * what input it expects,
  * what output it returns.

Example:

> `compute_basic_stats(file_path)` – Computes basic descriptive statistics for numeric columns in a CSV file.

#### 4. Example Interaction

* Provide an example of interaction with the agent
* This can be:

  * screenshots of the Dev UI, or
  * a clearly written example dialogue.

Screenshots are optional. Short explanations may be added if needed.

---

### 5.2 Agent Implementation (Python)

Your agent must include:

* a Python file implementing the agent,
* a system prompt aligned with the declared agent purpose,
* at least one tool that is actually invoked during interaction.

Code quality expectations:

* clear structure,
* meaningful function names,
* basic inline comments where appropriate.

---

## 6. Evaluation Criteria

Your submission will be evaluated according to the following criteria:

1. **Correct use of tools** (mandatory)
2. **Clear and well-defined agent purpose**
3. **Technical correctness** of the agent implementation
4. **Quality and clarity of the agent README.md**

This lab is evaluated as a **foundational exercise**. Simplicity and clarity are preferred over complexity.

---

## 7. Notes

* Keep the agent simple and focused on a single task
* The goal is to understand *how agents work*, not to build a complex application
* Screenshots are optional; a well-written example dialogue is sufficient
* This lab prepares you for future multi-agent scenarios

---

## 8. References

Links to example agents:

* Hello World Agent – [*Hello World Agent*](app/hello_world/)
* Dataset Data Analysis Agent – [*Dataset EDA*](app/dataset_eda/)

