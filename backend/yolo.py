import cv2
import os
import tempfile
from ultralytics import YOLO

# Load the YOLO model once at module level.
MODEL_PATH = "yolov8n.pt"  # Adjust to your model weights path
model = YOLO(MODEL_PATH)

def run_yolo_on_image(image_path):
    """
    Run YOLO inference on the image at image_path and return detections.
    Returns:
        A list of detections where each detection is a dict with keys:
        x1, y1, x2, y2, confidence, class.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Failed to read image file.")
    
    results = model(image)
    detections = []
    
    # Adjust parsing based on your ultralytics output.
    if results and results[0].boxes is not None:
        for box in results[0].boxes.boxes.tolist():
            detection = {
                "x1": box[0],
                "y1": box[1],
                "x2": box[2],
                "y2": box[3],
                "confidence": box[4],
                "class": box[5]
            }
            detections.append(detection)
    return detections
