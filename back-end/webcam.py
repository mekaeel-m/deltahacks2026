from flask import Flask
from flask_socketio import SocketIO, emit
import base64
import cv2
import numpy as np

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow cross-origin for dev

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('video_frame')
def handle_video_frame(data):
    # data is a base64-encoded JPEG data URL (e.g., "data:image/jpeg;base64,...")
    if data.startswith('data:image'):
        # Extract base64 part
        img_b64 = data.split(',')[1]
    else:
        img_b64 = data
    
    # Decode to bytes
    img_bytes = base64.b64decode(img_b64)
    
    # Convert to numpy array and decode with OpenCV
    nparr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is not None:
        # Process the frame here (example: grayscale conversion)
        processed_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Or apply any OpenCV/ML model, e.g., face detection
        
        # Optional: Encode and send processed frame back
        _, buffer = cv2.imencode('.jpg', processed_frame)
        processed_b64 = base64.b64encode(buffer).decode('utf-8')
        emit('processed_frame', f'data:image/jpeg;base64,{processed_b64}')
        
        print('Frame processed')
    else:
        print('Invalid frame received')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)