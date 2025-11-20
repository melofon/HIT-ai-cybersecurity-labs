# 🔧 **Assignment: Basic Anomaly Detection for Cybersecurity Logs**

This assignment consists of **four parts**.
Your goal is to build a small end-to-end anomaly detection pipeline for a cybersecurity-related dataset, analyze it, and visualize the detected anomalies in 2D.

---

## **1. Prepare a cybersecurity-related dataset**

You may either **(A) generate synthetic data** (e.g., login events, network flows, process activity, DNS queries), or **(B) download a small real dataset** from the internet (e.g., a reduced sample from UNSW-NB15, CIC-IDS, KDD-based sets, Windows event logs, etc.).

**Requirements:**

* Your data must correspond to at least **one MITRE ATT&CK technique** (e.g.,
  *T1078: Valid Accounts*,
  *T1110: Brute Force*,
  *T1059: Command-Line Execution*,
  *T1041: Exfiltration Over C2 Channel*, etc.).
* If you use an existing dataset, you **must downsample the attack cases** so that anomalies represent **a small minority** (1–5%). This is essential for Isolation Forest and similar unsupervised detectors.
* Your final DataFrame must contain:

  * at least **one time-based feature** (e.g., hour)
  * at least **one numeric feature** (e.g., bytes, duration)
  * at least **one categorical feature** (e.g., user, process, city, protocol)
  * optional label column (normal vs attack) for evaluation only.

---

## **2. Perform an exploratory data analysis (EDA)**

Create a short EDA section (similar in style to the provided EDA notebook).
Your EDA must include:

1. Basic dataset statistics:

   * number of rows
   * number of features
   * class distribution (normal vs anomalous, if available)

2. Visualizations (choose at least two):

   * histograms of key numeric features
   * countplots for categorical features
   * scatter plots or pairplots
   * time-based distribution (e.g., logins per hour)

3. A short (3–5 sentences) analytical summary describing the “normal” patterns in your dataset and what kinds of anomalies you expect to detect.

---

## **3. Apply an anomaly detection model**

Use **Isolation Forest** as the primary method.
If you want to experiment further, you may optionally try:

* **One-Class SVM**
* **Local Outlier Factor (LOF)**
* **Elliptic Envelope**
* **Simple clustering-based anomaly detection** (e.g., k-Means distance threshold)

Your anomaly detection step must include:

1. Preprocessing

   * Encode categorical features
   * Scale numeric features (e.g., StandardScaler)

2. Training

   * Train Isolation Forest on the full dataset or only on normal samples
   * Extract anomaly scores and predicted labels

3. Evaluation

   * Show a histogram of anomaly scores
   * Report how many anomalies the model detected
   * If the dataset includes ground truth labels, calculate simple metrics:
     accuracy, precision, recall (optional)

---

## **4. Visualize anomalies on a 2D projection**

Use a dimensionality-reduction method to project the dataset into 2D:

Choose one:

* **PCA** (recommended as baseline)
* **t-SNE** (better separation, slower)
* **UMAP** (good balance between speed and structure)

Your visualization must include:

1. A 2D scatter plot of your projected data
2. Coloring by **anomaly score** or **anomaly label**
3. A clear legend indicating normal vs anomalous points
4. A short explanation (2–3 sentences) of what the plot tells you about the structure of the data

Example:

> “Normal behavior forms a dense cluster in the central region, while anomalies appear as isolated points or small sparse groups at the edges of the projection.”

---

# ✔ **Deliverables**

Your final notebook must contain:

* Dataset generation or download code
* EDA section
* Anomaly detection with Isolation Forest (and optional second model)
* Dimensionality reduction + 2D anomaly visualization
* A short conclusion summarizing what your model was able to detect and why


