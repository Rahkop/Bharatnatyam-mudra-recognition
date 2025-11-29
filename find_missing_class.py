import numpy as np
import os

CLASSES_PATH = "dataset/classes.npy"
LABELS_PATH = "dataset/labels.npy"

# Load data
classes = np.load(CLASSES_PATH, allow_pickle=True)
labels = np.load(LABELS_PATH)

unique_ids = sorted(np.unique(labels))

print("\nTotal classes listed in classes.npy:", len(classes))
print("Total classes actually found in labels.npy:", len(unique_ids))

# find missing
missing_ids = [i for i in range(len(classes)) if i not in unique_ids]

print("\nMissing Class Index:", missing_ids)

if missing_ids:
    for i in missing_ids:
        print("Missing Mudra Name:", classes[i])
else:
    print("No missing classes!")
