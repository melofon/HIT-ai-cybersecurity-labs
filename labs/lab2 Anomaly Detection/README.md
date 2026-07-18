# 🔧 Lab 2 — Anomaly Detection for Cybersecurity Logs

This lab compares two complementary anomaly-detection approaches:

1. **Isolation Forest** — detects rare feature-space outliers.
2. **Autoencoder with categorical embeddings** — learns normal behavioral patterns and flags events with high reconstruction error.

The goal is not only to obtain predictions, but to compare what each model detects, where the models agree or disagree, and where human judgment is still required.

---

## 0. How to run the lab

From the repository root, run:

```bash
cd "labs/lab2 Anomaly Detection"
docker compose up --build
```

When the container starts, open JupyterLab at:

```text
http://127.0.0.1:8888/lab
```

If Jupyter asks for a token, copy the complete URL printed in the terminal.

After opening JupyterLab, navigate to the `work` directory.

### Recommended notebook order

1. `AnomalyDetectionComparison.ipynb` — **main Lab 2 notebook and required assignment**
2. `IsolationForest.ipynb` — supporting Isolation Forest example
3. `NetworkAttackAE.ipynb` — supporting autoencoder example using CICIDS data
4. `AE.ipynb` — additional autoencoder example
5. `EDA.ipynb` — exploratory data analysis example
6. `FakerExamlple.ipynb` — synthetic-data generation example

Start with `AnomalyDetectionComparison.ipynb` and run:

```text
Kernel → Restart Kernel and Run All Cells
```

The remaining notebooks are supporting examples unless your instructor explicitly assigns them.

### Stop the environment

Press `Ctrl+C` in the terminal running Docker, then run:

```bash
docker compose down
```

---

## 1. Prepare a cybersecurity-related dataset

Use either:

- synthetic events such as logins, network flows, process activity, DNS queries, or API calls; or
- a small real dataset such as CIC-IDS, UNSW-NB15, KDD-based data, or Windows event logs.

### Requirements

Your data must:

- correspond to at least one MITRE ATT&CK technique, for example:
  - **T1078 — Valid Accounts**
  - **T1110 — Brute Force**
  - **T1059 — Command and Scripting Interpreter**
  - **T1041 — Exfiltration Over C2 Channel**
- contain anomalies as a small minority, normally **1–5%**;
- contain at least:
  - one time-based feature;
  - two numeric features;
  - one categorical feature;
  - an optional ground-truth label used only for evaluation.

Do not train the autoencoder on attack-labelled records. The model must learn a baseline from normal behavior.

---

## 2. Exploratory data analysis

Include:

1. dataset dimensions and data types;
2. class distribution, if labels exist;
3. missing-value and infinite-value checks;
4. at least two visualizations;
5. a short description of expected normal behavior and likely anomalies.

---

## 3. Model A — Isolation Forest

### Required steps

1. Encode categorical features.
2. Scale numeric features.
3. Train an `IsolationForest`.
4. Produce anomaly scores and binary predictions.
5. Report:
   - number and proportion of anomalies;
   - score distribution;
   - precision, recall, F1 and confusion matrix when labels exist.

Isolation Forest is expected to work well for rare, isolated, numeric or tabular outliers.

---

## 4. Model B — Autoencoder with embeddings

The second model must combine:

- standardized numeric inputs;
- trainable embeddings for categorical fields;
- an encoder producing a low-dimensional latent representation;
- decoder outputs that reconstruct numeric and categorical inputs.

### Required steps

1. Split the data into train, validation and test partitions.
2. Train the autoencoder **only on normal training records**.
3. Calculate an anomaly score combining:
   - numeric reconstruction error;
   - categorical reconstruction loss.
4. Select the threshold using only normal validation data, for example the 95th or 99th percentile.
5. Produce predictions and evaluation metrics.
6. Extract the latent vectors as behavioral embeddings.

The autoencoder is expected to detect complex deviations from learned normal behavior, including unusual combinations of otherwise common values.

---

## 5. Compare the two methods

Create one comparison table containing at least:

| Measure | Isolation Forest | Autoencoder + embeddings |
|---|---:|---:|
| Detected anomalies | | |
| Precision | | |
| Recall | | |
| F1 score | | |
| False positives | | |
| False negatives | | |

Also calculate:

- **agreement rate** — percentage of records assigned the same label;
- anomalies detected by both models;
- anomalies detected only by Isolation Forest;
- anomalies detected only by the autoencoder.

Discuss at least three example records on which the models disagree.

### How to interpret the results

- **Precision** answers: Of all records flagged as anomalous, how many were actually attacks?
- **Recall** answers: Of all real attacks, how many were detected?
- **F1 score** balances precision and recall.
- **False positives** create unnecessary analyst workload and alert fatigue.
- **False negatives** represent attacks that the model missed.

A model should not be declared universally better based on one run. State instead which model performed better **on this dataset and with the current parameter settings**.

A typical conclusion may be:

> Isolation Forest achieved better quantitative results in this experiment because it detected the same attacks with fewer false positives. The autoencoder remains useful because it models learned behavioral patterns and may detect more subtle combinations in larger or more complex datasets.

---

## 6. Visualize anomalies and latent behavior

Produce:

1. a 2D PCA, t-SNE or UMAP plot based on the preprocessed feature space;
2. a second 2D plot based on the autoencoder latent representation;
3. colors or markers showing:
   - normal records;
   - true attacks, when labels exist;
   - Isolation Forest predictions;
   - autoencoder predictions.

Explain whether the latent representation separates behavioral anomalies more clearly than the original feature space.

Do not interpret overlap in a 2D projection as proof that a model failed. Dimensionality reduction compresses information and can hide separation that exists in the original feature space.

---

## 7. Human–AI decision task

For three high-scoring alerts:

1. inspect the original record;
2. identify the evidence supporting the alert;
3. explain whether the alert should be accepted, challenged or escalated;
4. identify possible false-positive explanations;
5. connect the event to a MITRE ATT&CK technique.

Remember:

> AI detects patterns. Humans validate context and make the operational decision.

---

# ✔ Deliverables

Submit one completed copy of `AnomalyDetectionComparison.ipynb` containing:

- data preparation;
- EDA;
- Isolation Forest;
- autoencoder with embeddings;
- threshold selection;
- quantitative comparison;
- original-space and latent-space visualizations;
- analysis of disagreements;
- MITRE ATT&CK interpretation;
- short conclusion.

The conclusion must answer:

1. Which model performed better and according to which measure?
2. Which model produced fewer false positives?
3. What types of anomalies were unique to each model?
4. Did embeddings improve behavioral separation?
5. Why should a SOC analyst avoid relying on one model alone?

## Student checklist

Before submission, confirm that:

- [ ] all notebook cells run from top to bottom without errors;
- [ ] both models were trained and evaluated;
- [ ] the comparison table is complete;
- [ ] false positives and false negatives were interpreted;
- [ ] at least three disagreement cases were discussed;
- [ ] the visualizations include readable labels and legends;
- [ ] the conclusion refers to the actual results rather than making a general claim;
- [ ] MITRE ATT&CK interpretation and the human decision task are included.
