import cv2
import os

def capture_faces():
    name = input("Enter the person's name: ").strip()
    dataset_dir = "datasets"
    person_dir = os.path.join(dataset_dir, name)

    os.makedirs(person_dir, exist_ok=True)
    print(f"[INFO] Directory created: {person_dir}")

    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cam.set(3, 640)
    cam.set(4, 480)

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    print("[INFO] Press 'c' to capture face or 'q' to quit")


    img_count = 0
    while True:
        ret, frame = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow("Capture Faces", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c') and len(faces) > 0:
            for (x, y, w, h) in faces:
                face_img = frame[y:y+h, x:x+w]
                img_path = os.path.join(person_dir, f"{name}_{img_count}.jpg")
                cv2.imwrite(img_path, face_img)
                print(f"[INFO] Saved {img_path}")
                img_count += 1
        elif key == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    print(f"[INFO] Captured {img_count} images for {name}")

if __name__ == "__main__":
    capture_faces()
