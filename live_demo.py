
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
    "camera_active": False,
}

prediction_lock = threading.Lock()
stop_event = threading.Event()
webcam_thread = None


def make_square_frame(frame):

    height, width = frame.shape[:2]

    size = max(height, width)

    top = (size - height) // 2
    bottom = size - height - top

    left = (size - width) // 2
    right = size - width - left

    square_frame = cv2.copyMakeBorder(
        frame,
        top,
        bottom,
        left,
        right,
        cv2.BORDER_CONSTANT,
        value=(0, 0, 0)
    )

    return square_frame, top, left, size


def landmarks_to_features(landmarks):

    xs = [lm.x for lm in landmarks]
    ys = [lm.y for lm in landmarks]
    zs = [lm.z for lm in landmarks]

    cx = np.mean(xs)
    cy = np.mean(ys)
    cz = np.mean(zs)

    vec = []

    for x, y, z in zip(xs, ys, zs):
        vec += [
            x - cx,
            y - cy,
            z - cz
        ]

    return np.array(
        vec,
        dtype=np.float32
    ).reshape(1, -1)


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

    with prediction_lock:
        latest_prediction["camera_active"] = True

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


                # Convert the frame into a square image without stretching.
                square_frame, pad_top, pad_left, square_size = (
                    make_square_frame(frame)
                )

                rgb = cv2.cvtColor(
                    square_frame,
                    cv2.COLOR_BGR2RGB
                )

                res = hands.process(rgb)

                label = "No hand"
                current_mudra = None
                confidence = None

                if res.multi_hand_landmarks:
                    landmarks = res.multi_hand_landmarks[0].landmark
                    features = landmarks_to_features(landmarks)

                    pred = model.predict(features)[0]
                    probabilities = model.predict_proba(features)[0]

                    class_index = np.where(model.classes_ == pred)[0][0]

                    confidence = float(probabilities[class_index])

                    current_mudra = str(classes[int(pred)])
                    label = (
                        f"{current_mudra} "
                        f"({confidence * 100:.1f}%)"
                    )

                    mp_draw.draw_landmarks(
                        square_frame,
                        res.multi_hand_landmarks[0],
                        mp_hands.HAND_CONNECTIONS,
                    )
                    original_frame = frame.copy()

                    # Remove the padding for normal webcam display.
                    frame = square_frame[
                        pad_top:pad_top + original_frame.shape[0],
                        pad_left:pad_left + original_frame.shape[1]
                    ].copy()

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

        with prediction_lock:
            latest_prediction["mudra"] = None
            latest_prediction["confidence"] = None
            latest_prediction["camera_active"] = False


def start_webcam():
    global webcam_thread

    if webcam_thread is not None and webcam_thread.is_alive():
        return

    stop_event.clear()

    webcam_thread = threading.Thread(
        target=run_webcam,
        daemon=True
    )

    webcam_thread.start()


def stop_webcam():
    stop_event.set()

def main():
    root = tk.Tk()

    MudraTutorChat(
        root,
        context_provider=get_current_prediction,
        on_close=stop_webcam,
        on_camera_start=start_webcam,
        on_camera_stop=stop_webcam,
    )

    root.mainloop()

    stop_webcam()


if __name__ == "__main__":
    main()



