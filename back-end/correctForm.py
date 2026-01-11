"""
Correct Form Module
Main module that integrates baseline collection and pose comparison.
Provides Flask endpoints for real-time pose accuracy checking.
"""

import os
import json
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from typing import Dict, Optional

from baseline_collector import BaselineCollector, collect_baseline_from_folder
from pose_comparator import PoseComparator, compare_pose_to_baseline, AccuracyLevel
from drawingLines import (
    process_image, 
    process_image_landmarks, 
    decode_base64_image,
    encode_image_to_base64,
    ARM_LINE_COLOR,
    ARM_LINE_THICKNESS,
    POINT_COLOR,
    POINT_RADIUS
)

app = Flask(__name__)
CORS(app)

# Global comparator instance (loaded on first use)
_comparator: Optional[PoseComparator] = None
_baseline_loaded = False

# Default paths
DEFAULT_BASELINE_FOLDER = os.path.join(os.path.dirname(__file__), 'baseline_images')
DEFAULT_BASELINE_FILE = os.path.join(os.path.dirname(__file__), 'output', 'baseline_data.json')

# Visualization colors
CORRECT_COLOR = (0, 255, 0)    # Green for correct pose
INCORRECT_COLOR = (0, 0, 255)  # Red for incorrect pose
WARNING_COLOR = (0, 165, 255)  # Orange for fair accuracy


def get_comparator() -> PoseComparator:
    """Get or create the global pose comparator instance."""
    global _comparator, _baseline_loaded
    
    if _comparator is None:
        _comparator = PoseComparator(baseline_path=DEFAULT_BASELINE_FILE)
    
    if not _baseline_loaded and os.path.exists(DEFAULT_BASELINE_FILE):
        try:
            _comparator.load_baseline()
            _baseline_loaded = True
            print(f"Baseline loaded from: {DEFAULT_BASELINE_FILE}")
        except Exception as e:
            print(f"Warning: Could not load baseline: {e}")
    
    return _comparator


def draw_comparison_overlay(image: np.ndarray, 
                            comparison_result, 
                            baseline_landmarks: Dict,
                            current_landmarks: Dict,
                            image_width: int,
                            image_height: int) -> np.ndarray:
    """
    Draw comparison overlay showing baseline vs current pose.
    
    Args:
        image: Image to draw on
        comparison_result: Result from pose comparison
        baseline_landmarks: Normalized baseline landmarks
        current_landmarks: Raw current landmarks (pixel coordinates)
        image_width: Width of the image
        image_height: Height of the image
        
    Returns:
        Image with overlay drawn
    """
    output = image.copy()
    
    # Determine color based on accuracy
    if comparison_result.accuracy_level == AccuracyLevel.EXCELLENT:
        line_color = CORRECT_COLOR
    elif comparison_result.accuracy_level in [AccuracyLevel.GOOD, AccuracyLevel.FAIR]:
        line_color = WARNING_COLOR
    else:
        line_color = INCORRECT_COLOR
    
    # Draw baseline pose (dashed lines in blue)
    baseline_color = (255, 200, 0)  # Cyan/light blue for baseline
    
    for arm_name in ['left_arm', 'right_arm']:
        baseline_arm = baseline_landmarks.get(arm_name, {})
        current_arm = current_landmarks.get(arm_name, {})
        
        # Draw baseline joints and lines
        baseline_points = {}
        for joint_name in ['shoulder', 'elbow', 'wrist']:
            if joint_name in baseline_arm:
                joint = baseline_arm[joint_name]
                px = int(joint['x'] * image_width)
                py = int(joint['y'] * image_height)
                baseline_points[joint_name] = (px, py)
                
                # Draw baseline point (hollow circle)
                cv2.circle(output, (px, py), POINT_RADIUS + 2, baseline_color, 2)
        
        # Draw baseline lines (dashed effect using small segments)
        if 'shoulder' in baseline_points and 'elbow' in baseline_points:
            draw_dashed_line(output, baseline_points['shoulder'], 
                           baseline_points['elbow'], baseline_color, 2)
        if 'elbow' in baseline_points and 'wrist' in baseline_points:
            draw_dashed_line(output, baseline_points['elbow'], 
                           baseline_points['wrist'], baseline_color, 2)
        
        # Draw current pose with accuracy-based color
        current_points = {}
        for joint_name in ['shoulder', 'elbow', 'wrist']:
            if joint_name in current_arm:
                joint = current_arm[joint_name]
                px = joint['x']
                py = joint['y']
                current_points[joint_name] = (px, py)
                
                # Check if this joint is accurate
                joint_accurate = True
                for fb in comparison_result.joint_feedback:
                    if fb.joint_name == joint_name and fb.arm_name == arm_name:
                        joint_accurate = fb.is_accurate
                        break
                
                point_color = CORRECT_COLOR if joint_accurate else INCORRECT_COLOR
                cv2.circle(output, (px, py), POINT_RADIUS, point_color, -1)
        
        # Draw current pose lines
        if 'shoulder' in current_points and 'elbow' in current_points:
            cv2.line(output, current_points['shoulder'], 
                    current_points['elbow'], line_color, ARM_LINE_THICKNESS)
        if 'elbow' in current_points and 'wrist' in current_points:
            cv2.line(output, current_points['elbow'], 
                    current_points['wrist'], line_color, ARM_LINE_THICKNESS)
    
    # Draw accuracy text
    accuracy_text = f"Accuracy: {comparison_result.overall_accuracy:.1f}%"
    cv2.putText(output, accuracy_text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, line_color, 2)
    
    status_text = "CORRECT" if comparison_result.is_accurate else "ADJUST FORM"
    cv2.putText(output, status_text, (10, 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, line_color, 2)
    
    return output


def draw_dashed_line(image: np.ndarray, 
                     pt1: tuple, 
                     pt2: tuple, 
                     color: tuple, 
                     thickness: int,
                     dash_length: int = 10):
    """Draw a dashed line between two points."""
    dist = np.sqrt((pt2[0] - pt1[0])**2 + (pt2[1] - pt1[1])**2)
    num_dashes = int(dist / (dash_length * 2))
    
    if num_dashes == 0:
        cv2.line(image, pt1, pt2, color, thickness)
        return
    
    for i in range(num_dashes):
        start_ratio = (i * 2 * dash_length) / dist
        end_ratio = ((i * 2 + 1) * dash_length) / dist
        
        if end_ratio > 1:
            end_ratio = 1
        
        start_pt = (
            int(pt1[0] + (pt2[0] - pt1[0]) * start_ratio),
            int(pt1[1] + (pt2[1] - pt1[1]) * start_ratio)
        )
        end_pt = (
            int(pt1[0] + (pt2[0] - pt1[0]) * end_ratio),
            int(pt1[1] + (pt2[1] - pt1[1]) * end_ratio)
        )
        
        cv2.line(image, start_pt, end_pt, color, thickness)


# ============== Flask Endpoints ==============

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    comparator = get_comparator()
    return jsonify({
        'status': 'healthy',
        'message': 'Form correction service is running',
        'baseline_loaded': _baseline_loaded
    })


@app.route('/collect-baseline', methods=['POST'])
def collect_baseline():
    """
    Collect baseline data from a folder of images.
    
    Accepts JSON:
        {
            "folder_path": "/path/to/baseline/images",  (optional, uses default)
            "output_path": "/path/to/output.json",      (optional)
            "aggregate_method": "average"               (optional: average, median, first, all)
        }
    
    Returns:
        JSON with baseline collection results
    """
    global _comparator, _baseline_loaded
    
    try:
        data = request.get_json() or {}
        
        folder_path = data.get('folder_path', DEFAULT_BASELINE_FOLDER)
        output_path = data.get('output_path', DEFAULT_BASELINE_FILE)
        aggregate_method = data.get('aggregate_method', 'average')
        
        # Collect baseline
        baseline_data = collect_baseline_from_folder(
            folder_path, 
            output_path, 
            aggregate_method
        )
        
        # Reload the comparator with new baseline
        _comparator = PoseComparator(baseline_path=output_path)
        _comparator.load_baseline()
        _baseline_loaded = True
        
        return jsonify({
            'success': True,
            'message': f"Baseline collected from {baseline_data['metadata']['num_images_processed']} images",
            'metadata': baseline_data['metadata'],
            'baseline_file': output_path
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/set-baseline', methods=['POST'])
def set_baseline():
    """
    Set baseline from a single image or load from file.
    
    Accepts:
        - JSON with base64 image: {"image": "base64_string"}
        - JSON with file path: {"baseline_file": "/path/to/baseline.json"}
        - Form data with image file
    """
    global _comparator, _baseline_loaded
    
    try:
        comparator = get_comparator()
        
        if request.is_json:
            data = request.get_json()
            
            # Load from file
            if 'baseline_file' in data:
                comparator.load_baseline(data['baseline_file'])
                _baseline_loaded = True
                return jsonify({
                    'success': True,
                    'message': f"Baseline loaded from {data['baseline_file']}"
                })
            
            # Create from single image
            if 'image' in data:
                image = decode_base64_image(data['image'])
                collector = BaselineCollector(None)
                result = process_image_landmarks(image)
                
                if not result.get('pose_detected'):
                    return jsonify({'error': 'No pose detected in image'}), 400
                
                h, w = image.shape[:2]
                normalized = collector.normalize_landmarks(result['landmarks'], w, h)
                angles = collector.calculate_joint_angles(normalized)
                
                baseline_data = {
                    'metadata': {'source': 'single_image'},
                    'baseline_landmarks': normalized,
                    'baseline_angles': angles
                }
                
                comparator.set_baseline(baseline_data)
                _baseline_loaded = True
                
                return jsonify({
                    'success': True,
                    'message': 'Baseline set from image',
                    'landmarks': normalized
                })
        
        # Handle file upload
        if 'image' in request.files:
            file = request.files['image']
            file_bytes = np.frombuffer(file.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            
            collector = BaselineCollector(None)
            result = process_image_landmarks(image)
            
            if not result.get('pose_detected'):
                return jsonify({'error': 'No pose detected in image'}), 400
            
            h, w = image.shape[:2]
            normalized = collector.normalize_landmarks(result['landmarks'], w, h)
            angles = collector.calculate_joint_angles(normalized)
            
            baseline_data = {
                'metadata': {'source': 'single_image'},
                'baseline_landmarks': normalized,
                'baseline_angles': angles
            }
            
            comparator.set_baseline(baseline_data)
            _baseline_loaded = True
            
            return jsonify({
                'success': True,
                'message': 'Baseline set from uploaded image',
                'landmarks': normalized
            })
        
        return jsonify({'error': 'No baseline source provided'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/compare-pose', methods=['POST'])
def compare_pose():
    """
    Compare a pose against the baseline and return accuracy flag.
    
    Accepts:
        - JSON with base64 image: {"image": "base64_string"}
        - Form data with image file
    
    Returns:
        JSON with accuracy flag and detailed feedback
    """
    try:
        comparator = get_comparator()
        
        if not _baseline_loaded:
            return jsonify({
                'error': 'No baseline loaded. Call /collect-baseline or /set-baseline first'
            }), 400
        
        image = None
        
        if request.is_json:
            data = request.get_json()
            if 'image' not in data:
                return jsonify({'error': 'No image provided'}), 400
            image = decode_base64_image(data['image'])
        
        elif 'image' in request.files:
            file = request.files['image']
            file_bytes = np.frombuffer(file.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        else:
            return jsonify({'error': 'No image provided'}), 400
        
        if image is None:
            return jsonify({'error': 'Failed to decode image'}), 400
        
        # Compare pose
        result = comparator.compare_image(image)
        flag = comparator.get_comparison_flag(result)
        
        return jsonify({
            'success': True,
            'flag': flag,
            'detailed_feedback': {
                'joint_feedback': [
                    {
                        'joint': fb.joint_name,
                        'arm': fb.arm_name,
                        'deviation': round(fb.deviation, 4),
                        'is_accurate': fb.is_accurate,
                        'message': fb.message
                    }
                    for fb in result.joint_feedback
                ],
                'angle_feedback': result.angle_feedback
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/compare-pose-visual', methods=['POST'])
def compare_pose_visual():
    """
    Compare pose and return image with visual overlay showing baseline vs current.
    
    Accepts:
        - JSON with base64 image: {"image": "base64_string"}
        - Form data with image file
    
    Returns:
        JSON with processed image and accuracy data
    """
    try:
        comparator = get_comparator()
        
        if not _baseline_loaded:
            return jsonify({
                'error': 'No baseline loaded. Call /collect-baseline or /set-baseline first'
            }), 400
        
        image = None
        
        if request.is_json:
            data = request.get_json()
            if 'image' not in data:
                return jsonify({'error': 'No image provided'}), 400
            image = decode_base64_image(data['image'])
        
        elif 'image' in request.files:
            file = request.files['image']
            file_bytes = np.frombuffer(file.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        else:
            return jsonify({'error': 'No image provided'}), 400
        
        if image is None:
            return jsonify({'error': 'Failed to decode image'}), 400
        
        h, w = image.shape[:2]
        
        # Get current landmarks
        landmark_result = process_image_landmarks(image)
        
        if not landmark_result.get('pose_detected'):
            return jsonify({'error': 'No pose detected in image'}), 400
        
        # Compare pose
        result = comparator.compare_pose(landmark_result['landmarks'], w, h)
        flag = comparator.get_comparison_flag(result)
        
        # Draw comparison overlay
        baseline_landmarks = comparator.baseline_data['baseline_landmarks']
        output_image = draw_comparison_overlay(
            image, result, baseline_landmarks, 
            landmark_result['landmarks'], w, h
        )
        
        # Encode output image
        processed_base64 = encode_image_to_base64(output_image)
        
        return jsonify({
            'success': True,
            'processed_image': f'data:image/png;base64,{processed_base64}',
            'flag': flag
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get-baseline', methods=['GET'])
def get_baseline():
    """Get the current baseline data."""
    try:
        comparator = get_comparator()
        
        if not _baseline_loaded:
            return jsonify({
                'error': 'No baseline loaded',
                'baseline_loaded': False
            }), 404
        
        return jsonify({
            'success': True,
            'baseline_loaded': True,
            'baseline_data': comparator.baseline_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/configure', methods=['POST'])
def configure():
    """
    Configure comparison thresholds.
    
    Accepts JSON:
        {
            "position_threshold": 0.1,    (0-1, normalized position deviation)
            "angle_threshold": 15.0,      (degrees)
            "accuracy_threshold": 75.0    (percentage to be considered accurate)
        }
    """
    try:
        comparator = get_comparator()
        data = request.get_json() or {}
        
        if 'position_threshold' in data:
            comparator.position_threshold = float(data['position_threshold'])
        if 'angle_threshold' in data:
            comparator.angle_threshold = float(data['angle_threshold'])
        if 'accuracy_threshold' in data:
            comparator.accuracy_threshold = float(data['accuracy_threshold'])
        
        return jsonify({
            'success': True,
            'config': {
                'position_threshold': comparator.position_threshold,
                'angle_threshold': comparator.angle_threshold,
                'accuracy_threshold': comparator.accuracy_threshold
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
    
    # get + send calculate score of pose compared to baseline
@app.route('/score', methods=['POST'])
def get_pose_score():
    """
    Quick endpoint to get just the accuracy percentage score.
    Accepts:
        - JSON with base64 image: {"image": "base64_string"}
        - Form data with image file
    Returns:
        JSON with accuracy percentage (0-100)
    """
    try:
        comparator = get_comparator()
        if not _baseline_loaded: 
            return jsonify({
                'score': 0, 
                'error': 'No baseline loaded'
            }), 400
        image = None
        
        if request.is_json:
            data = request.get_json() 
            if 'image' not in data:
                return jsonify({'score': 0, 'error': 'No image provided'}), 400
            image = decode_base64_image(data['image'])
        elif 'image' in request.files:
            file = request.files['image']
            file_bytes = np.frombuffer(file.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        else:
            return jsonify({'score': 0, 'error': 'No image provided'}), 400

        if image is None:
            return jsonify({'score': 0, 'error': 'Failed to decode image'}), 400
        
        # Compare pose and return the score 
        result = comparator.compare_image(image)
        return jsonify({
            'score': round(float(result.overall_accuracy),2)
        })
    except Exception as e:
        return jsonify({'score': 0, 'error': str(e)}), 500


def get_pose_score_detailed(landmarks, image_width, image_height):
    """
    Calculate accuracy score with detailed joint-level feedback.
    
    Args:
        landmarks: Dictionary with landmark data
            {
              "left_arm": {"shoulder": {x, y}, ...},
              "right_arm": {...}
            }
        image_width: Width of the image in pixels
        image_height: Height of the image in pixels
    
    Returns:
        Tuple: (score, accuracy_level, joints_feedback)
            score (float): Accuracy percentage 0-100
            accuracy_level (str): 'excellent', 'good', 'fair', or 'poor'
            joints_feedback (dict): Per-joint accuracy details
    """
    # check errMsg 
    errMsg = ""
    
    if not landmarks: # empty landmarks
        errMsg += "No landmarks provided!\n"
    
    comparator = get_comparator()
    
    if not _baseline_loaded:
        return 0, 'unknown', {}
    
    result = comparator.compare_pose(landmarks, image_width, image_height)
    
    # Build joint feedback dictionary
    # Format: {arm}_{joint} -> {is_accurate, deviation, message}
    joints_feedback = {}
    for fb in result.joint_feedback:
        key = f"{fb.arm_name}_{fb.joint_name}"
        joints_feedback[key] = {
            'is_accurate': bool(fb.is_accurate),
            'deviation': round(float(fb.deviation), 4),
            'message': fb.message,
            'arm': fb.arm_name,
            'joint': fb.joint_name
        }
    if not joints_feedback: # joints not
        errMsg += "Joint feedback failed!\n"
    
    return round(float(result.overall_accuracy), 2), result.accuracy_level.value, joints_feedback, errMsg


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))  # Use 5002 to avoid conflict with webcam.py (5001)
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Form Correction Flask App on port {port}")
    print("\nEndpoints:")
    print("  GET  /health              - Health check")
    print("  POST /collect-baseline    - Collect baseline from folder")
    print("  POST /set-baseline        - Set baseline from single image or file")
    print("  GET  /get-baseline        - Get current baseline data")
    print("  POST /score               - Get just the accuracy percentage (quick score)")
    print("  POST /compare-pose        - Compare pose and get accuracy flag")
    print("  POST /compare-pose-visual - Compare pose with visual overlay")
    print("  POST /configure           - Configure comparison thresholds")
    
    # Try to load default baseline on startup
    if os.path.exists(DEFAULT_BASELINE_FILE):
        try:
            get_comparator().load_baseline()
            print(f"\nDefault baseline loaded from: {DEFAULT_BASELINE_FILE}")
        except Exception as e:
            print(f"\nNote: Could not load default baseline: {e}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
