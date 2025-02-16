import cv2
import time
import os
from ultralytics import YOLO
import sqlite3

# ✅ Load the YOLO model once at module level
MODEL_PATH = "best.pt"  # Adjust this to your model path
model = YOLO(MODEL_PATH)

def run_yolo_on_frame(frame):
    """
    Run YOLO inference on the given frame and return detections.
    Args:
        frame: The OpenCV frame (image array).
    Returns:
        A list of detections where each detection is a dict with:
        {x1, y1, x2, y2, confidence, class}.
    """
    results = model(frame)
    detections = []

    # ✅ Process YOLO results and extract bounding boxes
    if results and results[0].boxes is not None:
        for box in results[0].boxes:
            detection = {
                "x1": float(box.xyxy[0][0]),  # x1
                "y1": float(box.xyxy[0][1]),  # y1
                "x2": float(box.xyxy[0][2]),  # x2
                "y2": float(box.xyxy[0][3]),  # y2
                "confidence": float(box.conf[0]),  # Confidence score
                "class": int(box.cls[0])  # Class ID
            }
            detections.append(detection)

    return detections

def process_video_stream(duration=600):
    """
    Capture frames from webcam and process them using YOLO for the given duration.
    Displays the real-time output with bounding boxes and class names.
    """
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Error: Could not open webcam.")
        return

    start_time = time.time()

    while (time.time() - start_time) < duration:
        ret, frame = cap.read()
        if not ret:
            print("❌ Error: Could not capture frame.")
            break

        # ✅ Run YOLO on the current frame
        detections = run_yolo_on_frame(frame)

        # ✅ Draw bounding boxes and labels
        results = model(frame)  # Run YOLO inference
        annotated_frame = results[0].plot()  # Adds boxes & labels

        # ✅ Display the live stream with YOLO detections
        cv2.imshow("YOLO Livestream", annotated_frame)

        # ✅ Find and print the highest confidence detection
        if detections:
            best_detection = max(detections, key=lambda d: d["confidence"])
            class_name = model.names[best_detection["class"]]
            confidence = best_detection["confidence"]
            print(f"Detected: {class_name} ({confidence:.2f})")

        # ✅ Press 'q' to exit early
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # ✅ Release resources
    cap.release()
    cv2.destroyAllWindows()

# ✅ Run the video processing function

