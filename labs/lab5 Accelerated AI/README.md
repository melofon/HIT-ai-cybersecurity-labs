# Lab 3.1 — Event-Driven Cybersecurity Pipeline with Kafka and Tracing

## Overview

In this laboratory assignment, you will build and explore a **simplified cybersecurity analysis pipeline** based on **event streaming and asynchronous processing**.

The goal of this lab is **not** to train advanced machine learning models, but to help you understand:

* how **high-load cybersecurity pipelines** are constructed,
* why **message queues** (Kafka) are used instead of direct function calls,
* how **pipeline stages are decoupled**,
* and how **distributed tracing** (Jaeger) helps to understand pipeline execution.

This lab serves as a **conceptual foundation** for later assignments, where GPU acceleration and performance monitoring will be added.

---

## Learning Objectives

After completing this lab, you should be able to:

* Explain why **queues are used in cybersecurity systems** (SIEM, SOC pipelines).
* Design a **multi-stage event-driven pipeline** using Kafka.
* Separate **data generation**, **processing**, and **analysis** stages.
* Understand the role of **distributed tracing** in complex pipelines.
* Map network events to **MITRE ATT&CK tactics and techniques**.
* Reason about **throughput, latency, and decoupling** in high-load systems.

---

## Conceptual Architecture

The pipeline you will work with has the following structure:

```
[ Data Generator ]
        |
        v
     Kafka
        |
        v
[ Packet Classifier ]
        |
        v
  Local Storage (CSV)
        |
        v
[ Statistics & Analysis ]
```

In parallel, **Jaeger** is used to trace how data flows through the pipeline.

Important distinction:

* **Kafka + Redpanda Console** → show *what data flows*
* **Jaeger** → shows *how the pipeline executes*

---

## Scenario

You are building a **toy cybersecurity analytics pipeline** that classifies network-like events according to the **MITRE ATT&CK framework**.

Each event represents a simplified “packet” or security-relevant activity (e.g., suspicious connection, authentication anomaly, scanning behavior).

The system must:

1. Ingest events asynchronously.
2. Process and classify them independently.
3. Store results for later analysis.
4. Provide visibility into pipeline execution.

This architecture mirrors real-world SOC / SIEM systems, only at a smaller and more understandable scale.

---

## Tools and Technologies

This lab uses the following components:

* **Docker Compose** — to run the full pipeline
* **Kafka (KRaft mode)** — message queue
* **Redpanda Console** — Kafka event viewer
* **Jaeger** — distributed tracing UI
* **JupyterLab** — development and execution environment
* **Python** — pipeline logic
* **CSV files** — persistent storage (for simplicity)

> We intentionally use CSV files instead of databases to keep the focus on **pipeline design**, not database administration.

---

## Repository Structure

```
.
├── compose.yml
├── notebooks/
│   └── 1. Mittre classification
│       ├── Producer.ipynb
│       ├── Consumer_Classifier.ipynb
│       └── Statistics.ipynb
├── data/
│   ├── raw_packets.csv
│   └── classified_packets.csv
└── README.md
```

* All notebooks are stored in a **local volume** mounted into JupyterLab.
* All intermediate and final results are stored locally.

---

## Pipeline Stages

### 1. Data Producer (`Producer.ipynb`)

Responsibilities:

* Read or generate synthetic network / packet-like events.
* Assign unique event IDs.
* Send events to a Kafka topic (e.g. `events.raw`).

Key idea:

> The producer **does not know** who will process the data.

---

### 2. Consumer & Classifier (`Consumer_Classifier.ipynb`)

Responsibilities:

* Consume events from Kafka.
* Perform lightweight classification.
* Map events to **MITRE ATT&CK tactics / techniques**.
* Emit traces to **Jaeger**.
* Save classification results to a local CSV file.

Key idea:

> The consumer works **independently** of the producer and can be scaled or replaced.

---

### 3. Statistics & Analysis (`Statistics.ipynb`)

Responsibilities:

* Load processed results from CSV.
* Compute basic statistics:

  * class distribution,
  * frequency of MITRE tactics,
  * processing counts.
* Visualize results using simple plots.

Key idea:

> Analysis happens **after** the pipeline, not inside it.

---

## Tracing with Jaeger

Each processed batch or event should generate **Jaeger spans**, for example:

* `kafka.consume`
* `classification`
* `storage.write`

Using Jaeger, you should be able to:

* See the **order of pipeline stages**.
* Observe **latency per stage**.
* Understand how a single event moves through the system.

Jaeger UI is available at:

```
http://localhost:16686
```

---

## Kafka Event Inspection

Kafka topics and messages can be inspected using **Redpanda Console**:

```
http://localhost:8080
```

You are encouraged to:

* Inspect raw events.
* Inspect classified events (if you use a second topic).
* Compare Kafka messages with stored CSV data.

---

## Assignment Tasks

### Mandatory Tasks

1. Run the full pipeline using `docker compose`.
2. Generate and publish events to Kafka.
3. Consume and classify events.
4. Store classification results locally.
5. Visualize basic statistics.
6. Inspect:

   * Kafka topics in Redpanda Console,
   * traces in Jaeger.

---

### Conceptual Questions (to be answered in the report)

* Why is Kafka used instead of direct function calls?
* What happens if the consumer is slower than the producer?
* How does tracing help debug pipeline behavior?
* Which pipeline stages could be scaled independently?
* How would this pipeline change in a real SOC system?

---

## Notes and Constraints

* This lab **does not require GPU acceleration**.
* Model quality is **not graded**.
* Focus on **architecture and reasoning**, not ML performance.
* Code clarity and pipeline correctness matter more than optimization.

---

## What Comes Next

In the next lab, this pipeline will be extended with:

* GPU-accelerated data processing (cuDF),
* accelerated model inference,
* performance metrics and monitoring,
* throughput and latency analysis.

---

## Key Takeaway

> **In cybersecurity, pipelines matter more than models.**
> This lab teaches you how such pipelines are built, observed, and reasoned about.
