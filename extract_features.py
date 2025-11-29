# extract_features.py
import os
import glob
import numpy as np
import cv2
import mediapipe as mp

# Use your existing dataset folder (it will accept names with parentheses)
DATA_ROOT = "dataset"
FEATURES_PATH = os.path.join(DATA_ROOT, "features.npy")
LABELS_PATH = os.path.join(DATA_ROOT, "labels.npy")
CLASSES_PATH = os.path.join(DATA_ROOT, "classes.npy")

# Find immediate subfolders inside dataset (these are your classes)
classes = sorted([d for d in os.listdir(DATA_ROOT) if os.path.isdir(os.path.join(DATA_ROOT, d))])
if not classes:
    raise SystemExit("No class folders found inside 'dataset'. Put your mudra folders directly inside dataset/")

class_to_id = {c: i for i, c in enumerate(classes)}
print("Found classes:", class_to_id)

mp_hands = mp.solutions.hands.Hands(static_image_mode=True, max_num_hands=1)
features = []
labels = []

def landmarks_to_features(landmarks):
    xs = [lm.x for lm in landmarks]
    ys = [lm.y for lm in landmarks]
    zs = [lm.z for lm in landmarks]
    cx, cy, cz = np.mean(xs), np.mean(ys), np.mean(zs)
    vec = []
    for x, y, z in zip(xs, ys, zs):
        vec += [x - cx, y - cy, z - cz]
    return np.array(vec, dtype=np.float32)

# Accept common image extensions
exts = ("*.jpg", "*.jpeg", "*.png", "*.bmp")

total = 0
for cls in classes:
    cls_dir = os.path.join(DATA_ROOT, cls)
    paths = []
    for e in exts:
        paths.extend(glob.glob(os.path.join(cls_dir, e)))
    count = 0
    for p in paths:
        img = cv2.imread(p)
        if img is None:
            continue
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        res = mp_hands.process(rgb)
        if not res.multi_hand_landmarks:
            continue
        lms = res.multi_hand_landmarks[0].landmark
        feat = landmarks_to_features(lms)
        features.append(feat)
        labels.append(class_to_id[cls])
        count += 1
        total += 1
    print(f"{cls}: extracted {count} samples")

mp_hands.close()

if total == 0:
    raise SystemExit("No hand landmarks were extracted. Check your images (crop to hands, improve lighting).")

features = np.stack(features, axis=0)
labels = np.array(labels, dtype=np.int64)

# Save files inside dataset/
np.save(FEATURES_PATH, features)
np.save(LABELS_PATH, labels)
np.save(CLASSES_PATH, np.array(classes, dtype=object))

print("Saved:", FEATURES_PATH, LABELS_PATH, CLASSES_PATH)
print("Shapes:", features.shape, labels.shape)
print("Classes (index -> name):")
for i, c in enumerate(classes):
    print(i, "->", c)


