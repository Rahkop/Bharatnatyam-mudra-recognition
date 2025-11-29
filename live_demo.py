import cv2
import joblib
import numpy as np
import mediapipe as mp
import time
import os

MODEL_PATH = "models/svm_mudra.pkl"
CLASSES_PATH = "dataset/classes.npy"

model = joblib.load(MODEL_PATH)
classes = np.load(CLASSES_PATH, allow_pickle=True)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)
mp_draw = mp.solutions.drawing_utils

def landmarks_to_features(landmarks):
    xs = [lm.x for lm in landmarks]
    ys = [lm.y for lm in landmarks]
    zs = [lm.z for lm in landmarks]
    cx, cy, cz = np.mean(xs), np.mean(ys), np.mean(zs)
    vec = []
    for x, y, z in zip(xs, ys, zs):
        vec += [x - cx, y - cy, z - cz]
    return np.array(vec, dtype=np.float32).reshape(1, -1)

cap = cv2.VideoCapture(0)

# reduce resolution for stability
cap.set(3, 640)
cap.set(4, 480)

prev = time.time()

while True:
    ok, frame = cap.read()
    if not ok:
        continue

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = hands.process(rgb)

    label = "No hand"
    confidence = 0

    if res.multi_hand_landmarks:
        lms = res.multi_hand_landmarks[0].landmark
        feats = landmarks_to_features(lms)
        pred = int(model.predict(feats)[0])
        conf = model.predict_proba(feats)[0][pred]
        label = f"{classes[pred]} ({conf*100:.1f}%)"

        mp_draw.draw_landmarks(
            frame,
            res.multi_hand_landmarks[0],
            mp_hands.HAND_CONNECTIONS
        )

    now = time.time()
    fps = 1 / (now - prev)
    prev = now

    cv2.putText(frame, label, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
    cv2.putText(frame, f"FPS: {int(fps)}", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,0), 2)

    cv2.imshow("Bharatanatyam Mudra Recognition", frame)

    k = cv2.waitKey(1)
    if k == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

