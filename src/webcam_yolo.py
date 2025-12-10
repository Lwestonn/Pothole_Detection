import time
from pathlib import Path

import cv2
from ultralytics import YOLO


def main():
    # Resolve model path relative to this file
    project_root = Path(__file__).resolve().parents[1]
    model_path = project_root / "models" / "best.pt"

    if not model_path.exists():
        print(f"Model not found at: {model_path}")
        print("Make sure best.pt is in the models folder.")
        return

    print(f"Loading model from: {model_path}")
    model = YOLO(str(model_path))

    # Open webcam (0 is default camera, change to 1 if you have multiple cameras)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Failed to open webcam. Try changing VideoCapture(0) to VideoCapture(1).")
        return

    print("Press 'q' or Esc to quit.")

    prev_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame from webcam.")
            break

        # Run YOLO inference on the frame
        # results is a list, we take the first element
        start_time = time.time()
        results = model(frame, verbose=False)
        infer_time = time.time() - start_time

        # Ultralytics adds boxes, labels, and confidences by default
        annotated_frame = results[0].plot()

        # Calculate FPS
        fps = 1.0 / infer_time if infer_time > 0 else 0.0
        fps_text = f"FPS: {fps:.1f}"

        # Draw FPS in the top left
        cv2.putText(
            annotated_frame,
            fps_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        # Show the frame
        cv2.imshow("YOLO Live Pothole Detection", annotated_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # 27 is Esc
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Webcam closed.")


if __name__ == "__main__":
    main()
