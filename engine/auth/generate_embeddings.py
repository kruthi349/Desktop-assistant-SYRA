import os
import cv2
import numpy as np
import joblib
from keras_facenet import FaceNet
from mtcnn import MTCNN

dataset_dir = "datasets"
embed_path = "embeddings.pkl"

embedder = FaceNet()
detector = MTCNN()

def extract_face(img):
    results = detector.detect_faces(img)
    if results:
        x, y, w, h = results[0]['box']
        x, y = abs(x), abs(y)
        face = img[y:y+h, x:x+w]
        face = cv2.resize(face, (160,160))
        return face
    return None

embeddings = {}
for person in os.listdir(dataset_dir):
    person_dir = os.path.join(dataset_dir, person)
    if not os.path.isdir(person_dir):
        continue
    person_embeds = []
    for img_name in os.listdir(person_dir):
        path = os.path.join(person_dir, img_name)
        img = cv2.imread(path)
        if img is None:
            continue
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face = extract_face(img_rgb)
        if face is not None:
            embedding = embedder.embeddings([face])[0]
            person_embeds.append(embedding)
    if person_embeds:
        embeddings[person] = np.mean(person_embeds, axis=0)
        print(f"[INFO] Processed {person}: {len(person_embeds)} images")

joblib.dump(embeddings, embed_path)
print(f"[INFO] Saved embeddings to {embed_path}")
