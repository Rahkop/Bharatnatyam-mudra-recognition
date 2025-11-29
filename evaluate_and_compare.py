# evaluate_and_compare.py
import os
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    accuracy_score,
)
import textwrap

# ----------------- CONFIG -----------------
MODEL_PATH = "models/svm_mudra.pkl"
CLASSES_PATH = "dataset/classes.npy"
FEATURES_PATH = "dataset/features.npy"
LABELS_PATH = "dataset/labels.npy"

# Path to the research paper you uploaded (local path)
RESEARCH_PAPER_PATH = "/mnt/data/AI-Powered_Bharatanatyam_Mudra_Identification_and_Description_System_Preserving_Heritage_Through_Technology.pdf"

# Set the paper accuracy (as a float between 0 and 1).
# Find the reported accuracy in the PDF and paste here, e.g. 0.92
PAPER_ACC = None  # <-- set this to the paper's reported accuracy (0.0 - 1.0) if you want comparison

# Output files
OUT_DIR = "results"
os.makedirs(OUT_DIR, exist_ok=True)

# ----------------- LOAD -----------------
print("Loading model and data...")
model = joblib.load(MODEL_PATH)
classes = np.load(CLASSES_PATH, allow_pickle=True)
X = np.load(FEATURES_PATH)
y = np.load(LABELS_PATH)

# If model expects different shaped features (e.g., single vs double-hand), adapt here.
# For usual case, the features.npy shape must match what the model was trained with.

# ----------------- PREDICT -----------------
print("Predicting...")
y_pred = model.predict(X)
acc = accuracy_score(y, y_pred)
print(f"\nOverall accuracy (on features.npy): {acc*100:.2f}%\n")

# ----------------- REPORT -----------------
print("Classification report (per-class):\n")
# align classes present in y (handles any removed/missing classes)
unique_labels = np.unique(y)
present_class_names = classes[unique_labels]
report = classification_report(y, y_pred, target_names=present_class_names, zero_division=0)
print(report)

# also compute precision/recall/f1 arrays
precision, recall, f1, support = precision_recall_fscore_support(y, y_pred, labels=unique_labels, zero_division=0)

# ----------------- PLOT: confusion matrix (raw + normalized) -----------------
cm = confusion_matrix(y, y_pred, labels=unique_labels)
cm_norm = cm.astype("float") / (cm.sum(axis=1)[:, np.newaxis] + 1e-9)

plt.figure(figsize=(14, 12))
sns.heatmap(cm, cmap="Blues", annot=False)
plt.title("Confusion Matrix (raw counts)")
plt.ylabel("True label")
plt.xlabel("Predicted label")
plt.tight_layout()
raw_cm_path = os.path.join(OUT_DIR, "confusion_matrix_raw.png")
plt.savefig(raw_cm_path, dpi=150)
print("Saved:", raw_cm_path)
plt.close()

plt.figure(figsize=(14, 12))
sns.heatmap(cm_norm, cmap="Blues", annot=False, vmin=0, vmax=1)
plt.title("Confusion Matrix (normalized by true class)")
plt.ylabel("True label")
plt.xlabel("Predicted label")
plt.tight_layout()
norm_cm_path = os.path.join(OUT_DIR, "confusion_matrix_norm.png")
plt.savefig(norm_cm_path, dpi=150)
print("Saved:", norm_cm_path)
plt.close()

# Optionally show a smaller confusion matrix with tick labels every N to avoid overlap
def plot_cm_zoomed(cm_matrix, class_names, fname, max_labels=40):
    n = len(class_names)
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(cm_matrix, ax=ax, cmap="Blues", cbar=True)
    step = 1
    if n > max_labels:
        step = max(1, n // max_labels)
    ax.set_xticks(np.arange(0, n, step) + 0.5)
    ax.set_xticklabels([class_names[i] for i in range(0, n, step)], rotation=90, fontsize=8)
    ax.set_yticks(np.arange(0, n, step) + 0.5)
    ax.set_yticklabels([class_names[i] for i in range(0, n, step)], rotation=0, fontsize=8)
    plt.tight_layout()
    fig.savefig(fname, dpi=150)
    plt.close()
    print("Saved:", fname)

plot_cm_zoomed(cm_norm, present_class_names, os.path.join(OUT_DIR, "confusion_matrix_norm_zoomed.png"))

# ----------------- PLOT: per-class Precision / Recall / F1 -----------------
indices = np.arange(len(present_class_names))
width = 0.25

plt.figure(figsize=(18, 10))
plt.bar(indices - width, precision, width=width, label="Precision")
plt.bar(indices, recall, width=width, label="Recall")
plt.bar(indices + width, f1, width=width, label="F1-score")
plt.xticks(indices, present_class_names, rotation=90, fontsize=9)
plt.ylim(0, 1.05)
plt.legend()
plt.title("Per-class Precision / Recall / F1")
plt.tight_layout()
metrics_path = os.path.join(OUT_DIR, "metrics_bar.png")
plt.savefig(metrics_path, dpi=150)
print("Saved:", metrics_path)
plt.close()

# ----------------- PLOT: support bar (samples per class) -----------------
plt.figure(figsize=(14,6))
plt.bar(indices, support)
plt.xticks(indices, present_class_names, rotation=90, fontsize=9)
plt.title("Support (number of test samples) per class")
plt.tight_layout()
support_path = os.path.join(OUT_DIR, "support_bar.png")
plt.savefig(support_path, dpi=150)
print("Saved:", support_path)
plt.close()

# ----------------- ACCURACY COMPARISON (your model vs paper) -----------------
if PAPER_ACC is None:
    print("\nPAPER_ACC is not set. If you want an accuracy comparison plot, set PAPER_ACC to the paper's reported value (e.g. 0.92).")
    # Show where the paper file is located for your convenience:
    if os.path.exists(RESEARCH_PAPER_PATH):
        print("Your uploaded research paper is at:", RESEARCH_PAPER_PATH)
        print("Open it and find the reported accuracy, then set PAPER_ACC variable inside this script.")
else:
    our = acc
    paper = float(PAPER_ACC)
    labels_comp = ["Your model", "Paper"]
    vals = [our*100, paper*100]
    plt.figure(figsize=(6,6))
    sns.barplot(x=labels_comp, y=vals)
    plt.ylim(0, 100)
    for i, v in enumerate(vals):
        plt.text(i, v+1, f"{v:.2f}%", ha='center', fontsize=12)
    plt.title("Accuracy Comparison")
    cmp_path = os.path.join(OUT_DIR, "accuracy_comparison.png")
    plt.tight_layout()
    plt.savefig(cmp_path, dpi=150)
    print("Saved:", cmp_path)

# ----------------- Save a short metrics summary txt -----------------
summary_path = os.path.join(OUT_DIR, "metrics_summary.txt")
with open(summary_path, "w") as f:
    f.write(f"Overall accuracy: {acc:.4f}\n\n")
    f.write("Per-class metrics:\n")
    for name, p, r, ff, s in zip(present_class_names, precision, recall, f1, support):
        f.write(f"{name}\tprecision={p:.3f}\trecall={r:.3f}\tf1={ff:.3f}\tsupport={s}\n")
print("Saved metrics summary to", summary_path)

print("\nAll plots and summary saved in folder:", OUT_DIR)
