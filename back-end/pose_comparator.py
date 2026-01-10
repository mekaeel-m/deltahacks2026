"""
Pose Comparator Module
Compares detected poses against a baseline and flags accuracy.
Provides detailed feedback on pose correctness.
"""

import os
import json
import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from drawingLines import process_image_landmarks
from baseline_collector import BaselineCollector


class AccuracyLevel(Enum):
    """Enum for pose accuracy levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"


@dataclass
class JointFeedback:
    """Feedback for a single joint."""
    joint_name: str
    arm_name: str
    deviation: float  # Normalized deviation (0-1)
    angle_deviation: Optional[float]  # Angle deviation in degrees
    is_accurate: bool
    message: str


@dataclass
class PoseComparisonResult:
    """Result of comparing a pose against baseline."""
    overall_accuracy: float  # 0-100 percentage
    accuracy_level: AccuracyLevel
    is_accurate: bool
    joint_feedback: List[JointFeedback]
    angle_feedback: Dict
    summary_message: str
    detailed_report: Dict


class PoseComparator:
    """Compares poses against a baseline and provides accuracy feedback."""
    
    def __init__(self, baseline_path: str = None, 
                 position_threshold: float = 0.1,
                 angle_threshold: float = 15.0,
                 accuracy_threshold: float = 75.0):
        """
        Initialize the pose comparator.
        
        Args:
            baseline_path: Path to the baseline JSON file
            position_threshold: Maximum allowed normalized position deviation (0-1)
            angle_threshold: Maximum allowed angle deviation in degrees
            accuracy_threshold: Minimum accuracy percentage to be considered "accurate"
        """
        self.baseline_path = baseline_path or os.path.join(
            os.path.dirname(__file__), 'output', 'baseline_data.json'
        )
        self.position_threshold = position_threshold
        self.angle_threshold = angle_threshold
        self.accuracy_threshold = accuracy_threshold
        self.baseline_data = None
        
    def load_baseline(self, path: str = None) -> Dict:
        """Load baseline data from file."""
        load_path = path or self.baseline_path
        
        if not os.path.exists(load_path):
            raise FileNotFoundError(f"Baseline file not found: {load_path}")
        
        with open(load_path, 'r') as f:
            self.baseline_data = json.load(f)
        
        return self.baseline_data
    
    def set_baseline(self, baseline_data: Dict):
        """Set baseline data directly."""
        self.baseline_data = baseline_data
    
    def normalize_landmarks(self, landmarks: Dict, image_width: int, image_height: int) -> Dict:
        """Normalize landmark coordinates to 0-1 range."""
        normalized = {}
        
        for arm_name, arm_data in landmarks.items():
            normalized[arm_name] = {}
            for joint_name, joint_data in arm_data.items():
                normalized[arm_name][joint_name] = {
                    'x': joint_data['x'] / image_width,
                    'y': joint_data['y'] / image_height,
                    'visibility': joint_data.get('visibility', 1.0)
                }
        
        return normalized
    
    def calculate_joint_angles(self, landmarks: Dict) -> Dict:
        """Calculate angles at each joint."""
        angles = {}
        
        for arm_name in ['left_arm', 'right_arm']:
            arm_data = landmarks.get(arm_name, {})
            
            if all(joint in arm_data for joint in ['shoulder', 'elbow', 'wrist']):
                shoulder = arm_data['shoulder']
                elbow = arm_data['elbow']
                wrist = arm_data['wrist']
                
                # Calculate elbow angle
                elbow_angle = self._calculate_angle(
                    (shoulder['x'], shoulder['y']),
                    (elbow['x'], elbow['y']),
                    (wrist['x'], wrist['y'])
                )
                
                # Calculate shoulder angle
                shoulder_angle = self._calculate_angle_from_vertical(
                    (shoulder['x'], shoulder['y']),
                    (elbow['x'], elbow['y'])
                )
                
                angles[arm_name] = {
                    'elbow_angle': elbow_angle,
                    'shoulder_angle': shoulder_angle
                }
        
        return angles
    
    def _calculate_angle(self, point1: Tuple[float, float], 
                         point2: Tuple[float, float], 
                         point3: Tuple[float, float]) -> float:
        """Calculate the angle at point2 formed by point1-point2-point3."""
        v1 = np.array([point1[0] - point2[0], point1[1] - point2[1]])
        v2 = np.array([point3[0] - point2[0], point3[1] - point2[1]])
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)
        
        return np.degrees(angle)
    
    def _calculate_angle_from_vertical(self, point1: Tuple[float, float], 
                                        point2: Tuple[float, float]) -> float:
        """Calculate the angle of the line from point1 to point2 relative to vertical."""
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        angle = np.degrees(np.arctan2(dx, dy))
        return angle
    
    def compare_pose(self, current_landmarks: Dict, 
                     image_width: int, 
                     image_height: int) -> PoseComparisonResult:
        """
        Compare current pose landmarks against the baseline.
        
        Args:
            current_landmarks: Landmark data from current frame (pixel coordinates)
            image_width: Width of the current image
            image_height: Height of the current image
            
        Returns:
            PoseComparisonResult with accuracy details
        """
        if self.baseline_data is None:
            self.load_baseline()
        
        baseline_landmarks = self.baseline_data['baseline_landmarks']
        baseline_angles = self.baseline_data['baseline_angles']
        
        # Normalize current landmarks
        normalized_current = self.normalize_landmarks(
            current_landmarks, image_width, image_height
        )
        
        # Calculate current angles
        current_angles = self.calculate_joint_angles(normalized_current)
        
        # Compare positions
        joint_feedback = []
        position_scores = []
        
        for arm_name in ['left_arm', 'right_arm']:
            baseline_arm = baseline_landmarks.get(arm_name, {})
            current_arm = normalized_current.get(arm_name, {})
            
            for joint_name in ['shoulder', 'elbow', 'wrist']:
                if joint_name in baseline_arm and joint_name in current_arm:
                    baseline_joint = baseline_arm[joint_name]
                    current_joint = current_arm[joint_name]
                    
                    # Calculate position deviation
                    dx = current_joint['x'] - baseline_joint['x']
                    dy = current_joint['y'] - baseline_joint['y']
                    deviation = np.sqrt(dx**2 + dy**2)
                    
                    # Account for baseline standard deviation if available
                    threshold = self.position_threshold
                    if 'std_x' in baseline_joint and 'std_y' in baseline_joint:
                        std = np.sqrt(baseline_joint['std_x']**2 + baseline_joint['std_y']**2)
                        threshold = max(threshold, std * 2)  # 2 standard deviations
                    
                    is_accurate = deviation <= threshold
                    score = max(0, 1 - (deviation / threshold)) * 100 if threshold > 0 else 100
                    position_scores.append(score)
                    
                    # Generate feedback message
                    if is_accurate:
                        message = f"{joint_name.capitalize()} position is correct"
                    else:
                        direction = self._get_direction(dx, dy)
                        message = f"Adjust {joint_name}: move {direction}"
                    
                    joint_feedback.append(JointFeedback(
                        joint_name=joint_name,
                        arm_name=arm_name,
                        deviation=deviation,
                        angle_deviation=None,
                        is_accurate=is_accurate,
                        message=message
                    ))
        
        # Compare angles
        angle_feedback = {}
        angle_scores = []
        
        for arm_name in ['left_arm', 'right_arm']:
            baseline_arm_angles = baseline_angles.get(arm_name, {})
            current_arm_angles = current_angles.get(arm_name, {})
            angle_feedback[arm_name] = {}
            
            for angle_name in ['elbow_angle', 'shoulder_angle']:
                if angle_name in baseline_arm_angles and angle_name in current_arm_angles:
                    baseline_angle = baseline_arm_angles[angle_name]
                    current_angle = current_arm_angles[angle_name]
                    
                    # Get baseline value (handle both dict and float formats)
                    if isinstance(baseline_angle, dict):
                        baseline_value = baseline_angle['value']
                        angle_std = baseline_angle.get('std', 0)
                    else:
                        baseline_value = baseline_angle
                        angle_std = 0
                    
                    # Calculate angle deviation
                    angle_deviation = abs(current_angle - baseline_value)
                    
                    # Adjust threshold based on standard deviation
                    threshold = max(self.angle_threshold, angle_std * 2)
                    
                    is_accurate = angle_deviation <= threshold
                    score = max(0, 1 - (angle_deviation / threshold)) * 100 if threshold > 0 else 100
                    angle_scores.append(score)
                    
                    # Generate feedback
                    if is_accurate:
                        message = f"{angle_name.replace('_', ' ').capitalize()} is correct"
                    else:
                        if current_angle > baseline_value:
                            adjustment = "decrease" if 'elbow' in angle_name else "lower"
                        else:
                            adjustment = "increase" if 'elbow' in angle_name else "raise"
                        message = f"Adjust {angle_name.replace('_', ' ')}: {adjustment} by {angle_deviation:.1f}°"
                    
                    angle_feedback[arm_name][angle_name] = {
                        'baseline': baseline_value,
                        'current': current_angle,
                        'deviation': angle_deviation,
                        'is_accurate': is_accurate,
                        'message': message
                    }
        
        # Calculate overall accuracy
        all_scores = position_scores + angle_scores
        overall_accuracy = np.mean(all_scores) if all_scores else 0
        
        # Determine accuracy level
        if overall_accuracy >= 90:
            accuracy_level = AccuracyLevel.EXCELLENT
        elif overall_accuracy >= 75:
            accuracy_level = AccuracyLevel.GOOD
        elif overall_accuracy >= 50:
            accuracy_level = AccuracyLevel.FAIR
        else:
            accuracy_level = AccuracyLevel.POOR
        
        is_accurate = overall_accuracy >= self.accuracy_threshold
        
        # Generate summary message
        if is_accurate:
            summary_message = f"Great form! Accuracy: {overall_accuracy:.1f}%"
        else:
            issues = [fb.message for fb in joint_feedback if not fb.is_accurate]
            angle_issues = []
            for arm_name, angles in angle_feedback.items():
                for angle_name, data in angles.items():
                    if not data['is_accurate']:
                        angle_issues.append(data['message'])
            
            all_issues = issues + angle_issues
            if all_issues:
                summary_message = f"Accuracy: {overall_accuracy:.1f}%. Issues: {'; '.join(all_issues[:3])}"
            else:
                summary_message = f"Accuracy: {overall_accuracy:.1f}%"
        
        return PoseComparisonResult(
            overall_accuracy=overall_accuracy,
            accuracy_level=accuracy_level,
            is_accurate=is_accurate,
            joint_feedback=joint_feedback,
            angle_feedback=angle_feedback,
            summary_message=summary_message,
            detailed_report={
                'position_scores': position_scores,
                'angle_scores': angle_scores,
                'normalized_landmarks': normalized_current,
                'current_angles': current_angles
            }
        )
    
    def _get_direction(self, dx: float, dy: float) -> str:
        """Get human-readable direction based on deviation."""
        directions = []
        
        if abs(dx) > 0.02:
            directions.append("left" if dx > 0 else "right")
        if abs(dy) > 0.02:
            directions.append("down" if dy > 0 else "up")
        
        return " and ".join(directions) if directions else "slightly"
    
    def compare_image(self, image: np.ndarray) -> PoseComparisonResult:
        """
        Compare pose in an image against the baseline.
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            PoseComparisonResult with accuracy details
        """
        result = process_image_landmarks(image)
        
        if not result.get('pose_detected') or not result.get('landmarks'):
            return PoseComparisonResult(
                overall_accuracy=0,
                accuracy_level=AccuracyLevel.INVALID,
                is_accurate=False,
                joint_feedback=[],
                angle_feedback={},
                summary_message="No pose detected in image",
                detailed_report={'error': 'No pose detected'}
            )
        
        image_height, image_width = image.shape[:2]
        
        return self.compare_pose(
            result['landmarks'],
            image_width,
            image_height
        )
    
    def compare_image_file(self, image_path: str) -> PoseComparisonResult:
        """
        Compare pose in an image file against the baseline.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            PoseComparisonResult with accuracy details
        """
        image = cv2.imread(image_path)
        if image is None:
            return PoseComparisonResult(
                overall_accuracy=0,
                accuracy_level=AccuracyLevel.INVALID,
                is_accurate=False,
                joint_feedback=[],
                angle_feedback={},
                summary_message=f"Could not read image: {image_path}",
                detailed_report={'error': 'Image read failed'}
            )
        
        return self.compare_image(image)
    
    def get_comparison_flag(self, result: PoseComparisonResult) -> Dict:
        """
        Get a simple flag dictionary for API responses.
        
        Args:
            result: PoseComparisonResult from comparison
            
        Returns:
            Dictionary with flag information
        """
        return {
            'is_accurate': result.is_accurate,
            'accuracy_percentage': round(result.overall_accuracy, 2),
            'accuracy_level': result.accuracy_level.value,
            'message': result.summary_message,
            'needs_correction': not result.is_accurate,
            'corrections': [
                {
                    'joint': fb.joint_name,
                    'arm': fb.arm_name,
                    'message': fb.message
                }
                for fb in result.joint_feedback if not fb.is_accurate
            ]
        }


def compare_pose_to_baseline(image: np.ndarray, 
                              baseline_path: str = None,
                              position_threshold: float = 0.1,
                              angle_threshold: float = 15.0) -> Dict:
    """
    Convenience function to compare a pose against baseline.
    
    Args:
        image: Input image as numpy array (BGR format)
        baseline_path: Path to baseline JSON file
        position_threshold: Maximum allowed position deviation
        angle_threshold: Maximum allowed angle deviation in degrees
        
    Returns:
        Dictionary with comparison results and flag
    """
    comparator = PoseComparator(
        baseline_path=baseline_path,
        position_threshold=position_threshold,
        angle_threshold=angle_threshold
    )
    
    result = comparator.compare_image(image)
    flag = comparator.get_comparison_flag(result)
    
    return {
        'flag': flag,
        'detailed_result': {
            'overall_accuracy': result.overall_accuracy,
            'accuracy_level': result.accuracy_level.value,
            'joint_feedback': [
                {
                    'joint': fb.joint_name,
                    'arm': fb.arm_name,
                    'deviation': fb.deviation,
                    'is_accurate': fb.is_accurate,
                    'message': fb.message
                }
                for fb in result.joint_feedback
            ],
            'angle_feedback': result.angle_feedback
        }
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare pose against baseline')
    parser.add_argument('--image', '-i', type=str, required=True,
                        help='Path to image to compare')
    parser.add_argument('--baseline', '-b', type=str, default=None,
                        help='Path to baseline JSON file')
    parser.add_argument('--position-threshold', '-p', type=float, default=0.1,
                        help='Position deviation threshold (0-1)')
    parser.add_argument('--angle-threshold', '-a', type=float, default=15.0,
                        help='Angle deviation threshold in degrees')
    
    args = parser.parse_args()
    
    comparator = PoseComparator(
        baseline_path=args.baseline,
        position_threshold=args.position_threshold,
        angle_threshold=args.angle_threshold
    )
    
    result = comparator.compare_image_file(args.image)
    flag = comparator.get_comparison_flag(result)
    
    print("\n=== Pose Comparison Result ===")
    print(f"Accurate: {flag['is_accurate']}")
    print(f"Accuracy: {flag['accuracy_percentage']}%")
    print(f"Level: {flag['accuracy_level']}")
    print(f"Message: {flag['message']}")
    
    if flag['corrections']:
        print("\nCorrections needed:")
        for correction in flag['corrections']:
            print(f"  - {correction['arm']} {correction['joint']}: {correction['message']}")
