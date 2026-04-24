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

* **AG2** (formerly AutoGen) — an open-source agent framework
* **Chainlit** — a web-based chat UI for interacting with agents
* **uv** — the dependency manager used inside the Docker image

The repository structure is as follows:

```
lab3/
├── .dockerignore
├── .gitignore
├── Dockerfile
├── compose.yml
├── app/
│   └── agent/
│       ├── app.py
│       └── README.md
├── .env
├── chainlit.md
├── pyproject.toml
├── uv.lock
└── README.md
```

The reference agent is implemented in `app/agent/`.

---

## 2. Setup and Running the Environment

The environment is provided in a ready-to-use Docker configuration. No local Python setup is required.

The Docker image contains the Python dependencies, and Compose runs Chainlit from
the container system environment.

Python dependencies are declared in `pyproject.toml` and locked by `uv.lock`.
Students do not install Python packages on the host machine.

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
docker build -t cybersec-agent-chainlit-lab3 .
```

### 2.4 Run the Application

Start the application using Docker Compose:

```bash
docker compose up
```

After startup, open the Chainlit UI in your browser at **http://localhost:8000**.

The project source code is mounted into the container at `/app`, but Chainlit itself
runs from `/chainlit-runtime`.
Runtime directories such as `.chainlit` and `.files` are container-only runtime
state and should not be committed to the repository.

### 2.5 Restarting After Code Changes

The Compose configuration always runs the reference agent from:

```text
app/agent/app.py
```

After changing Python code, restart the container:

```bash
docker compose down
docker compose up
```

### 2.6 Development Mode

The provided Compose setup is intentionally configured as a **development mode** environment.

Development mode means:

* the project directory is mounted from the host into the container via `.:/app`
* you edit files locally in the repository, while Chainlit runs inside Docker
* After changing Python code, restart the container to pick up the changes

This mode is convenient for experimentation because you do not need to rebuild the Docker image after every code change. Rebuilding is only needed when dependencies in `pyproject.toml` change.

### 2.7 Chainlit Welcome Screen (`chainlit.md`)

Chainlit reads `chainlit.md` as the welcome page shown in the browser before or during
a chat session. In this lab, the file is mounted into `/chainlit-runtime/chainlit.md`
and is displayed inside the containerized Chainlit UI.

For the course, `chainlit.md` is used as a short student-facing guide:

* remind the user what the current lab is about
* suggest first prompts for the reference agent
* point students to the required submission structure
* explain that tool calls are visible as expandable Chainlit steps

The agent itself also sends a Chainlit welcome message from `@cl.on_chat_start`
in `app/agent/app.py`. Use `chainlit.md` for static course instructions and the
agent welcome message for task-specific guidance from the running agent.

---

## 3. Student Task

You must design and implement **one simple LLM agent** to demonstrate that you understand:

* how an agent is structured,
* how a system prompt defines agent behavior,
* how tools are exposed and invoked by the agent.

Your agent does **not** need to solve a real cybersecurity problem. The task is purely educational and focuses on understanding agent concepts and mechanics.

### 3.1 Agent Location

Your agent must be implemented in the existing reference agent directory:

```
app/agent/
```

The directory already contains a working example. You may modify it directly or
replace it with your own simple agent implementation.

Your agent directory must contain at least an `app.py` file. In the container,
Compose runs it as `/app/app/agent/app.py`.

---

## 4. Mandatory Requirements

### 4.1 Tool Usage (Required)

Your agent **must use at least one tool**.

A tool is a Python function that the agent can explicitly call during interaction. The purpose of this requirement is to demonstrate the difference between:

* pure text generation, and
* agent-driven execution of functions.

The number and complexity of tools are **not important**. One simple tool is sufficient.

Agents that only generate text **without calling any tools will not be accepted**.

### 4.2 AG2 Tool Registration Pattern

AG2 supports multiple tool registration styles. In this laboratory, the provided examples use the simpler **single-agent tool pattern** that is also used in official AG2 examples.

Tools are attached directly to the agent through the `functions` argument:

```python
from autogen import ConversableAgent

agent = ConversableAgent(
  name="my_agent",
  system_message="You are a helpful assistant.",
  llm_config=llm_config,
  human_input_mode="NEVER",
  functions=[my_tool_function],
)
```

At runtime, AG2 handles the tool call flow internally. In Chainlit, tool invocations appear as expandable **Steps**.

Students may also use the more explicit caller/executor registration pattern if they want, but it is not required for this lab.

---

## 5. Required Deliverables

Your submission will be evaluated based on **two mandatory components** inside your agent directory:

### 5.1 `README.md` (Required)

Your agent directory must contain a `README.md` written in English with the following structure:

#### 1. Agent Name

* Any name you choose

#### 2. Agent Purpose

* A clear description of what the agent is designed to do
* This description must be written as a **technical task specification** for the agent's system prompt

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

  * screenshots of the Chainlit UI, or
  * a clearly written example dialogue.

Screenshots are optional. Short explanations may be added if needed.

---

### 5.2 Agent Implementation (Python)

Your agent must include:

* a Python file (`app.py`) implementing the agent,
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
* Tool calls are visible in the Chainlit UI as expandable **Steps**, making it easy to see when an agent invokes a function

---

## 8. References

Reference agent:

* Dataset Analysis Agent – [*app/agent*](app/agent/)
