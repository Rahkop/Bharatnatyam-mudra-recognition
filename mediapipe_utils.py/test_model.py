# test_model.py
import joblib, numpy as np
from sklearn.metrics import classification_report, confusion_matrix

MODEL_PATH = "models/rf_model.pkl"
TEST_PATH = "data/features_test.csv"   # or reuse split from training

model = joblib.load(MODEL_PATH)
data = np.genfromtxt(TEST_PATH, delimiter=",", skip_header=1)
X_test, y_test = data[:, :-1], data[:, -1].astype(int)

y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))
print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))

