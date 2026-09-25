Bharatanatyam Mudra Recognition
A real-time hand gesture recognition system that identifies Bharatanatyam mudras (hand gestures) from a webcam feed. Hand landmarks are extracted with MediaPipe, converted into a 63-dimensional feature vector, and classified using a trained SVM model.
Overview
The pipeline has three stages:
Feature extraction: each image in the dataset is passed through MediaPipe Hands, which detects 21 landmarks per hand (x, y, z). These are centered around the hand's mean position to produce a 63-value feature vector per sample.
Training: the extracted features are used to train a Support Vector Machine (RBF kernel) classifier with scikit-learn.
Inference: a live webcam demo runs the same landmark extraction and feeds it through the trained model to predict the mudra in real time, along with a confidence score and FPS counter.
Results
Trained on 51 mudra classes, the model reaches 98.8% overall accuracy on the held-out test split. Per-class precision, recall, and F1 are in `results/metrics_summary.txt`, and confusion matrix / metrics plots are in `results/`.
Tech stack
Python
MediaPipe for hand landmark detection
OpenCV for image and video I/O
scikit-learn (SVM, RBF kernel) for classification
NumPy for feature vector handling
joblib for model persistence
Matplotlib / Seaborn for evaluation plots
Pygame for the optional fullscreen intro screen
Project structure
```
Bharatnatyam-mudra-recognition/
├── dataset/                    # Mudra images, organized one folder per class
│   ├── classes.npy             # Saved class name list
│   ├── features.npy            # Extracted feature vectors
│   └── labels.npy              # Corresponding numeric labels
├── models/
│   └── svm_mudra.pkl           # Trained SVM model
├── results/                     # Confusion matrix, metrics plots, metrics_summary.txt
├── assets/                      # Images and audio used by intro_screen.py
├── extract_features.py         # Runs MediaPipe over dataset/, saves features + labels
├── train_quick.py              # Trains the SVM classifier and saves models/svm_mudra.pkl
├── evaluate_svm.py             # Evaluates the trained model, plots confusion matrix
├── live_demo.py                # Real-time webcam mudra recognition
├── intro_screen.py             # Optional fullscreen intro / launcher for live_demo.py
├── requirements.txt
└── README.md
```
Setup
```bash
git clone https://github.com/Rahkop/Bharatnatyam-mudra-recognition.git
cd Bharatnatyam-mudra-recognition
pip install -r requirements.txt
```
Usage
1. Extract features from the dataset
Place mudra images inside `dataset/`, one subfolder per class, then run:
```bash
python extract_features.py
```
This saves `features.npy`, `labels.npy`, and `classes.npy` inside `dataset/`.
2. Train the model
```bash
python train_quick.py
```
This trains an SVM (RBF kernel) on an 80/20 train-test split and saves the model to `models/svm_mudra.pkl`.
3. Evaluate
```bash
python evaluate_svm.py
```
Prints accuracy and a classification report, and plots the confusion matrix.
4. Run the live demo
```bash
python live_demo.py
```
Opens a webcam feed and overlays the predicted mudra and confidence in real time. Press `q` to quit.
Optionally, `python intro_screen.py` launches a fullscreen intro slideshow before starting `live_demo.py`.
Future improvements
Expand the dataset for better generalization
Explore deep learning approaches (CNN + LSTM) for sequence-based mudras
Add a guided-learning UI
Improve multi-hand and compound mudra recognition
Author
Rahithya Koppolu
