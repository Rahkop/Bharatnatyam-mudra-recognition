import numpy as np

# Load the saved class names
classes = np.load("dataset/classes.npy", allow_pickle=True)
print("Classes:", list(classes))

# Load and check feature and label arrays
features = np.load("dataset/features.npy")
labels = np.load("dataset/labels.npy")

print("Features shape:", features.shape)
print("Labels shape:", labels.shape)
