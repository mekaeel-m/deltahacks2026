"""
Flask app for arm pose detection and line drawing.
Uses MediaPipe Tasks API for efficient pose detection from various camera angles.
Draws lines: shoulder -> elbow -> wrist -> forefinger
"""

import time
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import os
import urllib.request

app = Flask(__name__)
CORS(app)

# Custom drawing specs for arm lines
ARM_LINE_COLOR = (0, 255, 0)  # Green in BGR
ARM_LINE_THICKNESS = 3
POINT_COLOR = (0, 0, 255)  # Red in BGR
POINT_RADIUS = 5

# Model paths
POSE_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'pose_landmarker.task')
HAND_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')

# Model URLs
POSE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
HAND_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"


def download_model(url, path):
    """Download a model file if it doesn't exist."""
    if not os.path.exists(path):
        print(f"Downloading model from {url}...")
        urllib.request.urlretrieve(url, path)
        print(f"Model saved to {path}")


# Download models on startup
download_model(POSE_MODEL_URL, POSE_MODEL_PATH)
download_model(HAND_MODEL_URL, HAND_MODEL_PATH)

# Cache landmarker instances globally to avoid reloading models on each request
_pose_landmarker = None
_hand_landmarker = None

def get_pose_landmarker():
    """Get or create cached pose landmarker instance."""
    global _pose_landmarker
    if _pose_landmarker is None:
        pose_options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=POSE_MODEL_PATH),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        _pose_landmarker = vision.PoseLandmarker.create_from_options(pose_options)
    return _pose_landmarker

def get_hand_landmarker():
    """Get or create cached hand landmarker instance."""
    global _hand_landmarker
    if _hand_landmarker is None:
        hand_options = vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=HAND_MODEL_PATH),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        _hand_landmarker = vision.HandLandmarker.create_from_options(hand_options)
    return _hand_landmarker
class PoseLandmark:
    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16

# Hand landmark indices
class HandLandmark:
    WRIST = 0
    INDEX_FINGER_TIP = 8


def decode_base64_image(base64_string):
    """Decode a base64 image string to a numpy array."""
    # Remove data URL prefix if present
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    image_data = base64.b64decode(base64_string)
    image = Image.open(BytesIO(image_data))
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def encode_image_to_base64(image):
    """Encode a numpy array image to base64 string."""
    _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer).decode('utf-8')


def get_landmark_pixel_coords(landmark, image_width, image_height):
    """Convert normalized landmark coordinates to pixel coordinates."""
    return (
        int(landmark.x * image_width),
        int(landmark.y * image_height)
    )


def draw_arm_lines(image, pose_landmarks, hand_landmarks_list, image_width, image_height):
    """
    Draw lines from shoulder to elbow to wrist to forefinger on both arms.
    
    Args:
        image: The image to draw on
        pose_landmarks: List of pose landmarks from MediaPipe
        hand_landmarks_list: List of hand landmarks from MediaPipe
        image_width: Width of the image
        image_height: Height of the image
    
    Returns:
        image: Image with arm lines drawn
        arms_detected: Boolean indicating if arms were detected
    """
    arms_detected = False
    
    if pose_landmarks is None or len(pose_landmarks) == 0:
        return image, arms_detected
    
    landmarks = pose_landmarks
    
    # Define arm landmark indices for MediaPipe Pose
    # Left arm: shoulder(11), elbow(13), wrist(15)
    # Right arm: shoulder(12), elbow(14), wrist(16)
    arm_configs = [
        {
            'name': 'left',
            'shoulder': PoseLandmark.LEFT_SHOULDER,
            'elbow': PoseLandmark.LEFT_ELBOW,
            'wrist': PoseLandmark.LEFT_WRIST,
        },
        {
            'name': 'right',
            'shoulder': PoseLandmark.RIGHT_SHOULDER,
            'elbow': PoseLandmark.RIGHT_ELBOW,
            'wrist': PoseLandmark.RIGHT_WRIST,
        }
    ]
    
    for arm in arm_configs:
        shoulder = landmarks[arm['shoulder']]
        elbow = landmarks[arm['elbow']]
        wrist = landmarks[arm['wrist']]
        
        # Check visibility/presence threshold (landmarks are visible enough)
        visibility_threshold = 0.5
        shoulder_vis = getattr(shoulder, 'visibility', getattr(shoulder, 'presence', 1.0))
        elbow_vis = getattr(elbow, 'visibility', getattr(elbow, 'presence', 1.0))
        wrist_vis = getattr(wrist, 'visibility', getattr(wrist, 'presence', 1.0))
        
        if (shoulder_vis > visibility_threshold and 
            elbow_vis > visibility_threshold and 
            wrist_vis > visibility_threshold):
            
            arms_detected = True
            
            # Get pixel coordinates
            shoulder_px = get_landmark_pixel_coords(shoulder, image_width, image_height)
            elbow_px = get_landmark_pixel_coords(elbow, image_width, image_height)
            wrist_px = get_landmark_pixel_coords(wrist, image_width, image_height)
            
            # Draw shoulder to elbow line
            cv2.line(image, shoulder_px, elbow_px, ARM_LINE_COLOR, ARM_LINE_THICKNESS)
            
            # Draw elbow to wrist line
            cv2.line(image, elbow_px, wrist_px, ARM_LINE_COLOR, ARM_LINE_THICKNESS)
            
            # Draw points at joints
            cv2.circle(image, shoulder_px, POINT_RADIUS, POINT_COLOR, -1)
            cv2.circle(image, elbow_px, POINT_RADIUS, POINT_COLOR, -1)
            cv2.circle(image, wrist_px, POINT_RADIUS, POINT_COLOR, -1)
            
            # Try to find the corresponding hand and draw line to forefinger
            forefinger_px = find_forefinger_for_wrist(
                wrist_px, hand_landmarks_list, image_width, image_height, arm['name']
            )
            
            if forefinger_px:
                # Draw wrist to forefinger line
                cv2.line(image, wrist_px, forefinger_px, ARM_LINE_COLOR, ARM_LINE_THICKNESS)
                cv2.circle(image, forefinger_px, POINT_RADIUS, POINT_COLOR, -1)
    
    return image, arms_detected




def find_forefinger_for_wrist(wrist_px, hand_landmarks_list, image_width, image_height, arm_side):
    """
    Find the forefinger tip that corresponds to the given wrist position.
    
    Args:
        wrist_px: Pixel coordinates of the wrist from pose detection
        hand_landmarks_list: List of detected hands (each is a list of landmarks)
        image_width: Width of the image
        image_height: Height of the image
        arm_side: 'left' or 'right' to help match the correct hand
    
    Returns:
        Pixel coordinates of the forefinger tip, or None if not found
    """
    if not hand_landmarks_list:
        return None
    
    best_hand = None
    min_distance = float('inf')
    
    for hand_landmarks in hand_landmarks_list:
        # Get wrist position from hand landmarks (landmark 0 is wrist)
        hand_wrist = hand_landmarks[HandLandmark.WRIST]
        hand_wrist_px = get_landmark_pixel_coords(hand_wrist, image_width, image_height)
        
        # Calculate distance between pose wrist and hand wrist
        distance = np.sqrt(
            (wrist_px[0] - hand_wrist_px[0])**2 + 
            (wrist_px[1] - hand_wrist_px[1])**2
        )
        
        # Use a threshold based on image size (10% of image diagonal)
        threshold = 0.1 * np.sqrt(image_width**2 + image_height**2)
        
        if distance < threshold and distance < min_distance:
            min_distance = distance
            best_hand = hand_landmarks
    
    if best_hand:
        # Get forefinger tip (INDEX_FINGER_TIP is landmark 8)
        forefinger = best_hand[HandLandmark.INDEX_FINGER_TIP]
        return get_landmark_pixel_coords(forefinger, image_width, image_height)
    
    return None


def process_image(image):
    """
    Process an image to detect arms and draw lines.
    
    Args:
        image: Input image as numpy array (BGR format)
    
    Returns:
        processed_image: Image with arm lines drawn
        result: Dictionary with detection results
    """
    image_height, image_width = image.shape[:2]
    
    # Convert BGR to RGB for MediaPipe
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Create MediaPipe Image
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    
    # Use cached landmarkers
    pose_landmarker = get_pose_landmarker()
    hand_landmarker = get_hand_landmarker()
    
    pose_landmarks = None
    hand_landmarks_list = []
    
    # Detect pose
    pose_results = pose_landmarker.detect(mp_image)
    if pose_results.pose_landmarks and len(pose_results.pose_landmarks) > 0:
        pose_landmarks = pose_results.pose_landmarks[0]  # Get first person's landmarks
    
    # Detect hands
    hand_results = hand_landmarker.detect(mp_image)
    if hand_results.hand_landmarks:
        hand_landmarks_list = hand_results.hand_landmarks
    
    # Draw arm lines
    processed_image, arms_detected = draw_arm_lines(
        image.copy(),
        pose_landmarks,
        hand_landmarks_list,
        image_width,
        image_height
    )
    
    # Prepare result data
    result = {
        'arms_detected': arms_detected,
        'pose_detected': pose_landmarks is not None,
        'hands_detected': len(hand_landmarks_list) > 0,
        'num_hands': len(hand_landmarks_list)
    }
    
    # Extract landmark coordinates if detected
    if pose_landmarks:
        result['landmarks'] = extract_arm_landmarks(
            pose_landmarks,
            hand_landmarks_list,
            image_width,
            image_height
        )
    
    return processed_image, result

def process_image_landmarks(image):
    

    """Extract arm landmarks from an image."""
    image_height, image_width = image.shape[:2]
    
    # Convert BGR to RGB for MediaPipe
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Create MediaPipe Image
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    
    # Use cached landmarkers
    pose_landmarker = get_pose_landmarker()
    hand_landmarker = get_hand_landmarker()
    
    pose_landmarks = None
    hand_landmarks_list = []
    
    # Detect pose
    pose_results = pose_landmarker.detect(mp_image)
    if pose_results.pose_landmarks and len(pose_results.pose_landmarks) > 0:
        pose_landmarks = pose_results.pose_landmarks[0]  # Get first person's landmarks
    
    # Detect hands
    hand_results = hand_landmarker.detect(mp_image)
    if hand_results.hand_landmarks:
        hand_landmarks_list = hand_results.hand_landmarks

    result = {
        'arms_detected': pose_landmarks is not None,
        'pose_detected': pose_landmarks is not None,
        'hands_detected': len(hand_landmarks_list) > 0,
        'num_hands': len(hand_landmarks_list)
    }

    # Extract arm landmarks if pose detected
    if pose_landmarks:
        result['landmarks'] = extract_arm_landmarks(
            pose_landmarks,
            hand_landmarks_list,
            image_width,
            image_height
        )

    return result


def extract_arm_landmarks(pose_landmarks, hand_landmarks_list, image_width, image_height):
    """Extract arm landmark coordinates for API response."""
    landmarks = pose_landmarks
    
    arm_data = {
        'left_arm': {},
        'right_arm': {}
    }
    
    def get_visibility(landmark):
        return getattr(landmark, 'visibility', getattr(landmark, 'presence', 1.0))
    
    # Left arm
    left_shoulder = landmarks[PoseLandmark.LEFT_SHOULDER]
    left_elbow = landmarks[PoseLandmark.LEFT_ELBOW]
    left_wrist = landmarks[PoseLandmark.LEFT_WRIST]
    
    if get_visibility(left_shoulder) > 0.5:
        arm_data['left_arm']['shoulder'] = {
            'x': int(left_shoulder.x * image_width),
            'y': int(left_shoulder.y * image_height),
            'visibility': get_visibility(left_shoulder)
        }
    if get_visibility(left_elbow) > 0.5:
        arm_data['left_arm']['elbow'] = {
            'x': int(left_elbow.x * image_width),
            'y': int(left_elbow.y * image_height),
            'visibility': get_visibility(left_elbow)
        }
    if get_visibility(left_wrist) > 0.5:
        arm_data['left_arm']['wrist'] = {
            'x': int(left_wrist.x * image_width),
            'y': int(left_wrist.y * image_height),
            'visibility': get_visibility(left_wrist)
        }
    
    # Right arm
    right_shoulder = landmarks[PoseLandmark.RIGHT_SHOULDER]
    right_elbow = landmarks[PoseLandmark.RIGHT_ELBOW]
    right_wrist = landmarks[PoseLandmark.RIGHT_WRIST]
    
    if get_visibility(right_shoulder) > 0.5:
        arm_data['right_arm']['shoulder'] = {
            'x': int(right_shoulder.x * image_width),
            'y': int(right_shoulder.y * image_height),
            'visibility': get_visibility(right_shoulder)
        }
    if get_visibility(right_elbow) > 0.5:
        arm_data['right_arm']['elbow'] = {
            'x': int(right_elbow.x * image_width),
            'y': int(right_elbow.y * image_height),
            'visibility': get_visibility(right_elbow)
        }
    if get_visibility(right_wrist) > 0.5:
        arm_data['right_arm']['wrist'] = {
            'x': int(right_wrist.x * image_width),
            'y': int(right_wrist.y * image_height),
            'visibility': get_visibility(right_wrist)
        }
    
    return arm_data


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'Arm detection service is running'})


@app.route('/detect-arms', methods=['POST'])
def detect_arms():
    """
    Detect arms in an image and draw lines from shoulder to forefinger.
    
    Accepts:
        - JSON with base64 encoded image: {"image": "base64_string"}
        - Form data with image file: file field named "image"
    
    Returns:
        JSON with:
        - processed_image: base64 encoded image with arm lines drawn
        - detection_result: object with detection details
    """
    try:
        image = None
        filename = "processed_image.png"  # default
        
        # Check for JSON input (base64 image)
        if request.is_json:
            data = request.get_json()
            if 'image' not in data:
                return jsonify({'error': 'No image provided in JSON'}), 400
            image = decode_base64_image(data['image'])
        
        # Check for file upload
        elif 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            filename = file.filename  # Use the input filename
            # Read image from file
            file_bytes = np.frombuffer(file.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        else:
            return jsonify({'error': 'No image provided. Send base64 JSON or file upload'}), 400
        
        if image is None:
            return jsonify({'error': 'Failed to decode image'}), 400
        
        # Process the image
        processed_image, result = process_image(image)

        cv2.imwrite(f"output/{filename}", processed_image)
        
        # Encode processed image to base64
        processed_base64 = encode_image_to_base64(processed_image)
        
        return jsonify({
            'success': True,
            'processed_image': f'data:image/png;base64,{processed_base64}',
            'detection_result': result
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/detect-arms-raw', methods=['POST'])
def detect_arms_raw():
    """
    Detect arms and return the processed image directly (not base64).
    Useful for direct image display or saving.
    """
    print("Starting timer...")
    start_time = time.perf_counter()  # High-precision start time

    try:
    
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        
        # Read image from file
        file_bytes = np.frombuffer(file.read(), np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        filename = file.filename  # Use the input filename
        
        if image is None:
            return jsonify({'error': 'Failed to decode image'}), 400
        
        # Process the image
        processed_image, _ = process_image(image)

        cv2.imwrite(f"output/{filename}", processed_image)
        
        # Encode to PNG and return
        _, buffer = cv2.imencode('.png', processed_image)

        end_time = time.perf_counter()  # High-precision end time
        elapsed = end_time - start_time

        print(f"Execution finished in {elapsed:.6f} seconds.")
        
        return send_file(
            BytesIO(buffer.tobytes()),
            mimetype='image/png',
            as_attachment=False
        )
    
    except Exception as e:
        end_time = time.perf_counter()  # High-precision end time
        elapsed = end_time - start_time

        print(f"Execution finished in {elapsed:.6f} seconds.")
        return jsonify({'error': str(e)}), 500


@app.route('/landmarks-only', methods=['POST'])
def landmarks_only():
    """
    Detect arms and return only the landmark coordinates (no image processing).
    Useful for applications that want to draw their own visualizations.
    """
    print("Starting timer...")
    start_time = time.perf_counter()  # High-precision start time

    try:
        image = None
        
        if request.is_json:
            data = request.get_json()
            if 'image' not in data:
                return jsonify({'error': 'No image provided in JSON'}), 400
            image = decode_base64_image(data['image'])
        
        elif 'image' in request.files:
            file = request.files['image']
            file_bytes = np.frombuffer(file.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        else:
            return jsonify({'error': 'No image provided'}), 400
        
        if image is None:
            return jsonify({'error': 'Failed to decode image'}), 400
        
        result = process_image_landmarks(image)

        end_time = time.perf_counter()  # High-precision end time
        elapsed = end_time - start_time
        print(f"Execution finished in {elapsed:.6f} seconds.")
        
        return jsonify({
            'success': True,
            'detection_result': result
        })
    
    except Exception as e:

        end_time = time.perf_counter()  # High-precision end time
        elapsed = end_time - start_time
        print(f"Execution finished in {elapsed:.6f} seconds.")

        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Arm Detection Flask App on port {port}")
    print("Endpoints:")
    print("  GET  /health - Health check")
    print("  POST /detect-arms - Detect arms and return base64 image")
    print("  POST /detect-arms-raw - Detect arms and return raw image")
    print("  POST /landmarks-only - Return only landmark coordinates")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
