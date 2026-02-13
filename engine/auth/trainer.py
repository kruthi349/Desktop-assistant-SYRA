import os
import cv2
import numpy as np
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.preprocessing import LabelEncoder
from tensorflow.keras.models import load_model
import joblib

DATASET_DIR = "datasets"
MODEL_PATH = "face_recognition_model.h5"
ENCODER_PATH = "label_encoder.pkl"

def load_dataset(img_size=(128, 128)):
    X, y = [], []
    for person in os.listdir(DATASET_DIR):
        person_dir = os.path.join(DATASET_DIR, person)
        if not os.path.isdir(person_dir):
            continue
        for img_name in os.listdir(person_dir):
            img_path = os.path.join(person_dir, img_name)
            img = cv2.imread(img_path)
            if img is None:
                continue
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = cv2.resize(img, img_size)
            X.append(img)
            y.append(person)
    return np.array(X), np.array(y)

def train_model():
    print("[INFO] Loading dataset...")
    X, y = load_dataset()
    print(f"[INFO] Loaded {len(X)} images from {len(set(y))} classes")

    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    y_cat = to_categorical(y_encoded)

    X = X / 255.0  # normalize

    datagen = ImageDataGenerator(
        rotation_range=10,
        zoom_range=0.1,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True
    )
    datagen.fit(X)

    model = Sequential([
        Conv2D(32, (3,3), activation='relu', input_shape=(128,128,3)),
        MaxPooling2D(2,2),
        Conv2D(64, (3,3), activation='relu'),
        MaxPooling2D(2,2),
        Conv2D(128, (3,3), activation='relu'),
        MaxPooling2D(2,2),
        Flatten(),
        Dense(128, activation='relu'),
        Dropout(0.5),
        Dense(len(set(y)), activation='softmax')
    ])

    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

    print("[INFO] Training model...")
    model.fit(datagen.flow(X, y_cat, batch_size=16), epochs=10, verbose=1)

    model.save(MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)
    print(f"[INFO] Model saved to {MODEL_PATH}")
    print(f"[INFO] Label encoder saved to {ENCODER_PATH}")

if __name__ == "__main__":
    train_model()
