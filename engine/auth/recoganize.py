import cv2
import numpy as np
from keras_facenet import FaceNet
from mtcnn import MTCNN
import joblib
from sklearn.metrics.pairwise import cosine_similarity

embedder = FaceNet()
detector = MTCNN()
embeddings = joblib.load("engine/auth/embeddings.pkl")

def AuthenticateFace(threshold=0.55):
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cam.set(3, 640)
    cam.set(4, 480)

    print("[INFO] Press ESC to exit")

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = detector.detect_faces(img_rgb)

        for r in results:
            x, y, w, h = r['box']
            x, y = abs(x), abs(y)
            face = img_rgb[y:y+h, x:x+w]
            face = cv2.resize(face, (160,160))
            embedding = embedder.embeddings([face])[0]

            best_match = "Unknown"
            best_score = -1

            for name, stored_embed in embeddings.items():
                score = cosine_similarity(
                    [embedding], [stored_embed]
                )[0][0]
                if score > best_score:
                    best_score = score
                    best_match = name

            color = (0,0,255)
            if best_score >= threshold:
                color = (0,255,0)
                label = f"{best_match} ({best_score:.2f})"
                flag = 1
            else:
                label = f"Unknown ({best_score:.2f})"
                flag = 0

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, label, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            if flag == 1:
                print(f"Authenticated: {best_match}")
                cam.release()
                cv2.destroyAllWindows()
                return (1, best_match)

        cv2.imshow("Face Recognition", frame)
        if cv2.waitKey(10) & 0xFF == 27:
            break

    cam.release()
    cv2.destroyAllWindows()
    return 0

if __name__ == "__main__":
    AuthenticateFace()
