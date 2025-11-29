import os
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

# -------------------------------------
# 1. Read mudra names from folder names
# -------------------------------------
DATASET_DIR = "dataset"   # your folders like Pataka, Tripataka, etc.
mudra_names = sorted([
    f for f in os.listdir(DATASET_DIR)
    if os.path.isdir(os.path.join(DATASET_DIR, f))
])

np.save("dataset/classes.npy", mudra_names)
print("Mudra Names:", mudra_names)

# -------------------------------------
# 2. Load feature array and numeric labels
# -------------------------------------
X = np.load("dataset/features.npy")
y = np.load("dataset/labels.npy")

print("Total samples:", len(y))

# -------------------------------------
# 3. Split
# -------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# -------------------------------------
# 4. Train High-Accuracy Model (SVM RBF)
# -------------------------------------
model = SVC(kernel="rbf", probability=True, C=10, gamma="scale")
model.fit(X_train, y_train)

# -------------------------------------
# 5. Evaluate
# -------------------------------------
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

print("\nModel Accuracy: {:.2f}%".format(acc * 100))
print("\nClassification Report:\n",
      classification_report(y_test, y_pred, target_names=mudra_names))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# -------------------------------------
# 6. Save model
# -------------------------------------
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/svm_mudra.pkl")
print("\nModel saved as models/svm_mudra.pkl")



