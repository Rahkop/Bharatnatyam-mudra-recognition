import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# -----------------------------
# Load model + dataset
# -----------------------------
MODEL_PATH = "models/svm_mudra.pkl"
CLASSES_PATH = "dataset/classes.npy"
X_PATH = "dataset/features.npy"
Y_PATH = "dataset/labels.npy"

model = joblib.load(MODEL_PATH)
classes = np.load(CLASSES_PATH, allow_pickle=True)
X = np.load(X_PATH)
y = np.load(Y_PATH)

# -----------------------------
# Predict
# -----------------------------
y_pred = model.predict(X)

acc = accuracy_score(y, y_pred)
print(f"\nFinal Accuracy: {acc*100:.2f}%")

print("\nClassification Report:\n")
print(classification_report(y, y_pred, target_names=classes))

# -----------------------------
# CONFUSION MATRIX
# -----------------------------
cm = confusion_matrix(y, y_pred)
plt.figure(figsize=(14, 12))
sns.heatmap(cm, annot=False, cmap="Blues")
plt.title("Confusion Matrix - Mudra Recognition")
plt.xlabel("Predicted")
plt.ylabel("True")
plt.show()

# -----------------------------
# ACCURACY BAR GRAPH
# -----------------------------
plt.bar(["Accuracy"], [acc])
plt.ylim(0, 1)
plt.title("Model Accuracy")
plt.show()
