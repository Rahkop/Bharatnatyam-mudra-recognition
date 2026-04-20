Bharatanatyam Mudra Recognition using MediaPipe

Project Overview

This project implements a Bharatanatyam hand gesture (mudra) recognition system using MediaPipe and machine learning. It detects hand landmarks from images and uses them to train a classifier that can recognize different mudras. The system also includes a real-time webcam demo for live prediction.

Features

* Hand landmark detection using MediaPipe
* Dataset-based training for multiple mudras
* Machine learning model using Random Forest
* Real-time webcam-based mudra recognition
* Modular and easy-to-understand code structure

Project Structure

bharatanatyam-mudra-recognition/
│
├── dataset/                # Contains image data organized by class
├── models/                 # Stores trained models and scripts
│   ├── train_model.py
│   ├── test_model.py
│   ├── live_demo.py
│   └── requirements.txt
├── mp-env/                 # Virtual environment (not required to share)
└── README.md

Requirements

Install dependencies using:
pip install -r models/requirements.txt

Main libraries used:

* mediapipe
* opencv-python
* numpy
* scikit-learn
* joblib

Dataset Preparation

* Place dataset inside the dataset/ folder.
* Each mudra should have its own folder.
* Example:
    dataset/
    pataka/
    tripataka/
    katakamukha/
* Each folder should contain 10–30 images for initial testing.

How to Run

1. Activate Virtual Environment

Windows:
mp-env\Scripts\activate

2. Train the Model

cd models
python train_model.py

3. Test the Model

python test_model.py

4. Run Live Demo

python live_demo.py

Output

* Trained model is saved in the models/ folder.
* Terminal displays training accuracy.
* Live demo opens webcam and shows predicted mudra.

Current Status

* Dataset preparation completed
* Feature extraction using MediaPipe implemented
* Model training and evaluation working
* Real-time detection implemented

Future Improvements

* Use larger dataset for better accuracy
* Implement deep learning (CNN + LSTM)
* Add UI similar to Duolingo for guided learning
* Improve multi-hand and complex mudra recognition

Author
Rahithya Koppolu
