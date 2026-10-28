
import cv2
import joblib
import numpy as np
import mediapipe as mp
import time
import threading
import tkinter as tk

from ui.chat_interface import MudraTutorChat


MODEL_PATH = "models/svm_mudra.pkl"
CLASSES_PATH = "dataset/classes.npy"

# Load your existing trained model and class names.
model = joblib.load(MODEL_PATH)
classes = np.load(CLASSES_PATH, allow_pickle=True)

# Shared state: latest webcam prediction for the AI tutor.
latest_prediction = {
    "mudra": None,
    "confidence": None,
}

prediction_lock = threading.Lock()
stop_event = threading.Event()


def landmarks_to_features(landmarks):
    """Convert 21 hand landmarks into the existing 63-value feature vector."""
    xs = [lm.x for lm in landmarks]
    ys = [lm.y for lm in landmarks]
    zs = [lm.z for lm in landmarks]

    cx, cy, cz = np.mean(xs), np.mean(ys), np.mean(zs)

    vec = []
    for x, y, z in zip(xs, ys, zs):
        vec += [x - cx, y - cy, z - cz]

    return np.array(vec, dtype=np.float32).reshape(1, -1)


def get_current_prediction():
    """Safely return the most recent prediction to the chat interface."""
    with prediction_lock:
        return latest_prediction.copy()


def run_webcam():
    """Run the existing live mudra recognition in a background thread."""
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        cap.release()
        return

    prev = time.time()

    try:
        with mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
        ) as hands:

            while not stop_event.is_set():
                ok, frame = cap.read()

                if not ok:
                    time.sleep(0.02)
                    continue

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = hands.process(rgb)

                label = "No hand"
                current_mudra = None
                confidence = None

                if res.multi_hand_landmarks:
                    landmarks = res.multi_hand_landmarks[0].landmark
                    features = landmarks_to_features(landmarks)

                    pred = int(model.predict(features)[0])
                    probabilities = model.predict_proba(features)[0]
                    confidence = float(probabilities[pred])

                    current_mudra = str(classes[pred])
                    label = (
                        f"{current_mudra} "
                        f"({confidence * 100:.1f}%)"
                    )

                    mp_draw.draw_landmarks(
                        frame,
                        res.multi_hand_landmarks[0],
                        mp_hands.HAND_CONNECTIONS,
                    )

                # Publish the latest prediction for the AI tutor.
                with prediction_lock:
                    latest_prediction["mudra"] = current_mudra
                    latest_prediction["confidence"] = confidence

                now = time.time()
                fps = 1 / max(now - prev, 1e-6)
                prev = now

                cv2.putText(
                    frame, label, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                    (0, 255, 0), 2,
                )
                cv2.putText(
                    frame, f"FPS: {int(fps)}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (255, 255, 0), 2,
                )

                cv2.imshow("Bharatanatyam Mudra Recognition", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    stop_event.set()
                    break

    finally:
        cap.release()
        cv2.destroyAllWindows()


def main():
    # Start webcam recognition in the background.
    webcam_thread = threading.Thread(
        target=run_webcam,
        daemon=True,
    )
    webcam_thread.start()

    # Keep Tkinter running on the main thread.
    root = tk.Tk()

    MudraTutorChat(
        root,
        context_provider=get_current_prediction,
        on_close=stop_event.set,
    )

    root.mainloop()
    stop_event.set()


if __name__ == "__main__":
    main()
