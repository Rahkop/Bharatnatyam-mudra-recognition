import os
import cv2
import numpy as np
import mediapipe as mp
import glob

DATASET = "dataset"
MUDRA_NAME = "Swastikam(1)"   # Missing class
SAVE_FEATURES = "dataset/features.npy"
SAVE_LABELS = "dataset/labels.npy"
SAVE_CLASSES = "dataset/classes.npy"

# Load previous data
features = np.load(SAVE_FEATURES)
labels = np.load(SAVE_LABELS)
classes = np.load(SAVE_CLASSES, allow_pickle=True)

# Map class to index
class_to_id = {c: i for i, c in enumerate(classes)}
missing_id = class_to_id[MUDRA_NAME]

print("Fixing missing mudra:", MUDRA_NAME, "→ class index", missing_id)

# Prepare mediapipe
mp_hands = mp.solutions.hands.Hands(static_image_mode=True, max_num_hands=1)

def lm_to_features(lms):
    xs = [lm.x for lm in lms]
    ys = [lm.y for lm in lms]
    zs = [lm.z for lm in lms]
    cx, cy, cz = np.mean(xs), np.mean(ys), np.mean(zs)
    vec = []
    for x, y, z in zip(xs, ys, zs):
        vec += [x - cx, y - cy, z - cz]
    return np.array(vec, dtype=np.float32)

# Process images in Swastikam folder
folder_path = os.path.join(DATASET, MUDRA_NAME)
img_paths = []
for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
    img_paths.extend(glob.glob(os.path.join(folder_path, ext)))

added_count = 0

for path in img_paths:
    img = cv2.imread(path)
    if img is None:
        continue

    # Automatic brightening + rotation attempts
    attempts = [
        img,
        cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE),
        cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE),
        cv2.rotate(img, cv2.ROTATE_180),
        cv2.convertScaleAbs(img, alpha=1.3, beta=30),
    ]

    detected = False
    for attempt in attempts:
        rgb = cv2.cvtColor(attempt, cv2.COLOR_BGR2RGB)
        res = mp_hands.process(rgb)

        if res.multi_hand_landmarks:
            feat = lm_to_features(res.multi_hand_landmarks[0].landmark)
            features = np.vstack([features, feat])
            labels = np.append(labels, missing_id)
            added_count += 1
            detected = True
            break

    if not detected:
        print("Failed to detect hand in:", path)

# Save updated dataset
np.save(SAVE_FEATURES, features)
np.save(SAVE_LABELS, labels)
np.save(SAVE_CLASSES, classes)

print("\nAdded", added_count, "new samples for", MUDRA_NAME)
print("New features shape:", features.shape)
print("New labels shape:", labels.shape)
