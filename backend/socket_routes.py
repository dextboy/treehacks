import os
import base64
import tempfile
from flask_socketio import emit
from yolo import run_yolo_on_image

def register_socket_events(socketio):

    @socketio.on('detect_image')
    def handle_detect_image(data):
        # Expecting data to be a dictionary with an 'image' key containing the Base64 string.
        image_data = data.get('image')
        if not image_data:
            emit('error', {'error': 'No image data provided'})
            return

        # If the data URL header exists, strip it.
        if ',' in image_data:
            header, encoded = image_data.split(',', 1)
        else:
            encoded = image_data

        try:
            image_bytes = base64.b64decode(encoded)
        except Exception as e:
            emit('error', {'error': 'Failed to decode image', 'details': str(e)})
            return

        # Write the image bytes to a temporary file.
        temp_dir = tempfile.mkdtemp()
        image_path = os.path.join(temp_dir, 'temp_image.jpg')
        try:
            with open(image_path, 'wb') as f:
                f.write(image_bytes)

            detections = run_yolo_on_image(image_path)
        except Exception as e:
            emit('error', {'error': 'Detection failed', 'details': str(e)})
            detections = []
        finally:
            # Clean up temporary file and directory.
            if os.path.exists(image_path):
                os.remove(image_path)
            if os.path.isdir(temp_dir):
                os.rmdir(temp_dir)

        emit('detection_results', {'detections': detections})
