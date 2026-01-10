"""
Baseline Collector Module
Automates the collection of pose data from a folder of baseline images.
Processes images to extract joint landmarks and stores them as the baseline for comparison.
"""

import os
import json
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from drawingLines import process_image_landmarks, decode_base64_image


class BaselineCollector:
    """Collects and manages baseline pose data from reference images."""
    
    def __init__(self, baseline_folder: str, output_path: str = None):
        """
        Initialize the baseline collector.
        
        Args:
            baseline_folder: Path to folder containing baseline images
            output_path: Path to save the baseline data JSON file
        """
        self.baseline_folder = baseline_folder
        self.output_path = output_path or os.path.join(
            os.path.dirname(__file__), 'output', 'baseline_data.json'
        )
        self.supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        
    def get_image_files(self) -> List[str]:
        """Get all supported image files from the baseline folder."""
        if not os.path.exists(self.baseline_folder):
            raise FileNotFoundError(f"Baseline folder not found: {self.baseline_folder}")
        
        image_files = []
        for filename in os.listdir(self.baseline_folder):
            ext = os.path.splitext(filename)[1].lower()
            if ext in self.supported_extensions:
                image_files.append(os.path.join(self.baseline_folder, filename))
        
        return sorted(image_files)
    
    def extract_landmarks_from_image(self, image_path: str) -> Optional[Dict]:
        """
        Extract pose landmarks from a single image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing landmark data or None if detection failed
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                print(f"Warning: Could not read image: {image_path}")
                return None
            
            result = process_image_landmarks(image)
            
            if result.get('pose_detected') and result.get('landmarks'):
                return {
                    'filename': os.path.basename(image_path),
                    'image_shape': {
                        'height': image.shape[0],
                        'width': image.shape[1]
                    },
                    'landmarks': result['landmarks'],
                    'arms_detected': result.get('arms_detected', False),
                    'hands_detected': result.get('hands_detected', False),
                    'num_hands': result.get('num_hands', 0)
                }
            else:
                print(f"Warning: No pose detected in: {image_path}")
                return None
                
        except Exception as e:
            print(f"Error processing {image_path}: {str(e)}")
            return None
    
    def normalize_landmarks(self, landmarks: Dict, image_width: int, image_height: int) -> Dict:
        """
        Normalize landmark coordinates to 0-1 range for scale-invariant comparison.
        
        Args:
            landmarks: Raw landmark data with pixel coordinates
            image_width: Width of the source image
            image_height: Height of the source image
            
        Returns:
            Normalized landmark data
        """
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
        """
        Calculate angles at each joint for pose comparison.
        
        Args:
            landmarks: Landmark data (normalized or pixel coordinates)
            
        Returns:
            Dictionary of joint angles in degrees
        """
        angles = {}
        
        for arm_name in ['left_arm', 'right_arm']:
            arm_data = landmarks.get(arm_name, {})
            
            if all(joint in arm_data for joint in ['shoulder', 'elbow', 'wrist']):
                shoulder = arm_data['shoulder']
                elbow = arm_data['elbow']
                wrist = arm_data['wrist']
                
                # Calculate elbow angle (angle at elbow between shoulder and wrist)
                elbow_angle = self._calculate_angle(
                    (shoulder['x'], shoulder['y']),
                    (elbow['x'], elbow['y']),
                    (wrist['x'], wrist['y'])
                )
                
                # Calculate shoulder angle (angle of upper arm relative to vertical)
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
        """
        Calculate the angle at point2 formed by point1-point2-point3.
        
        Returns angle in degrees (0-180).
        """
        v1 = np.array([point1[0] - point2[0], point1[1] - point2[1]])
        v2 = np.array([point3[0] - point2[0], point3[1] - point2[1]])
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)
        
        return np.degrees(angle)
    
    def _calculate_angle_from_vertical(self, point1: Tuple[float, float], 
                                        point2: Tuple[float, float]) -> float:
        """
        Calculate the angle of the line from point1 to point2 relative to vertical.
        
        Returns angle in degrees (-180 to 180).
        """
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        
        # Angle from vertical (positive y is down in image coordinates)
        angle = np.degrees(np.arctan2(dx, dy))
        
        return angle
    
    def collect_baseline(self, aggregate_method: str = 'average') -> Dict:
        """
        Collect baseline data from all images in the baseline folder.
        
        Args:
            aggregate_method: How to aggregate multiple images ('average', 'median', 'first', 'all')
            
        Returns:
            Baseline data dictionary
        """
        image_files = self.get_image_files()
        
        if not image_files:
            raise ValueError(f"No supported images found in {self.baseline_folder}")
        
        print(f"Found {len(image_files)} images in baseline folder")
        
        all_landmarks = []
        all_angles = []
        processed_files = []
        
        for image_path in image_files:
            print(f"Processing: {os.path.basename(image_path)}")
            result = self.extract_landmarks_from_image(image_path)
            
            if result:
                # Normalize landmarks
                normalized = self.normalize_landmarks(
                    result['landmarks'],
                    result['image_shape']['width'],
                    result['image_shape']['height']
                )
                
                # Calculate angles
                angles = self.calculate_joint_angles(normalized)
                
                all_landmarks.append(normalized)
                all_angles.append(angles)
                processed_files.append(result['filename'])
        
        if not all_landmarks:
            raise ValueError("No valid pose data extracted from any images")
        
        print(f"Successfully processed {len(all_landmarks)} images")
        
        # Aggregate the data
        if aggregate_method == 'first':
            aggregated_landmarks = all_landmarks[0]
            aggregated_angles = all_angles[0]
        elif aggregate_method == 'all':
            aggregated_landmarks = all_landmarks
            aggregated_angles = all_angles
        else:
            aggregated_landmarks = self._aggregate_landmarks(all_landmarks, aggregate_method)
            aggregated_angles = self._aggregate_angles(all_angles, aggregate_method)
        
        baseline_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'source_folder': self.baseline_folder,
                'num_images_processed': len(all_landmarks),
                'processed_files': processed_files,
                'aggregate_method': aggregate_method
            },
            'baseline_landmarks': aggregated_landmarks,
            'baseline_angles': aggregated_angles,
            'individual_samples': [
                {'landmarks': lm, 'angles': ang} 
                for lm, ang in zip(all_landmarks, all_angles)
            ] if aggregate_method != 'all' else None
        }
        
        return baseline_data
    
    def _aggregate_landmarks(self, all_landmarks: List[Dict], method: str) -> Dict:
        """Aggregate multiple landmark samples into a single baseline."""
        aggregated = {}
        
        for arm_name in ['left_arm', 'right_arm']:
            aggregated[arm_name] = {}
            
            for joint_name in ['shoulder', 'elbow', 'wrist']:
                x_values = []
                y_values = []
                vis_values = []
                
                for landmarks in all_landmarks:
                    if arm_name in landmarks and joint_name in landmarks[arm_name]:
                        joint = landmarks[arm_name][joint_name]
                        x_values.append(joint['x'])
                        y_values.append(joint['y'])
                        vis_values.append(joint.get('visibility', 1.0))
                
                if x_values:
                    if method == 'median':
                        aggregated[arm_name][joint_name] = {
                            'x': float(np.median(x_values)),
                            'y': float(np.median(y_values)),
                            'visibility': float(np.median(vis_values)),
                            'std_x': float(np.std(x_values)),
                            'std_y': float(np.std(y_values))
                        }
                    else:  # average
                        aggregated[arm_name][joint_name] = {
                            'x': float(np.mean(x_values)),
                            'y': float(np.mean(y_values)),
                            'visibility': float(np.mean(vis_values)),
                            'std_x': float(np.std(x_values)),
                            'std_y': float(np.std(y_values))
                        }
        
        return aggregated
    
    def _aggregate_angles(self, all_angles: List[Dict], method: str) -> Dict:
        """Aggregate multiple angle samples into a single baseline."""
        aggregated = {}
        
        for arm_name in ['left_arm', 'right_arm']:
            aggregated[arm_name] = {}
            
            for angle_name in ['elbow_angle', 'shoulder_angle']:
                values = []
                
                for angles in all_angles:
                    if arm_name in angles and angle_name in angles[arm_name]:
                        values.append(angles[arm_name][angle_name])
                
                if values:
                    if method == 'median':
                        aggregated[arm_name][angle_name] = {
                            'value': float(np.median(values)),
                            'std': float(np.std(values))
                        }
                    else:  # average
                        aggregated[arm_name][angle_name] = {
                            'value': float(np.mean(values)),
                            'std': float(np.std(values))
                        }
        
        return aggregated
    
    def save_baseline(self, baseline_data: Dict) -> str:
        """
        Save baseline data to a JSON file.
        
        Args:
            baseline_data: The baseline data to save
            
        Returns:
            Path to the saved file
        """
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        with open(self.output_path, 'w') as f:
            json.dump(baseline_data, f, indent=4)
        
        print(f"Baseline data saved to: {self.output_path}")
        return self.output_path
    
    def load_baseline(self, path: str = None) -> Dict:
        """
        Load baseline data from a JSON file.
        
        Args:
            path: Path to the baseline file (uses default if not provided)
            
        Returns:
            Baseline data dictionary
        """
        load_path = path or self.output_path
        
        if not os.path.exists(load_path):
            raise FileNotFoundError(f"Baseline file not found: {load_path}")
        
        with open(load_path, 'r') as f:
            return json.load(f)


def collect_baseline_from_folder(folder_path: str, 
                                  output_path: str = None,
                                  aggregate_method: str = 'average') -> Dict:
    """
    Convenience function to collect baseline data from a folder.
    
    Args:
        folder_path: Path to folder containing baseline images
        output_path: Path to save the baseline JSON (optional)
        aggregate_method: How to aggregate ('average', 'median', 'first', 'all')
        
    Returns:
        Baseline data dictionary
    """
    collector = BaselineCollector(folder_path, output_path)
    baseline_data = collector.collect_baseline(aggregate_method)
    collector.save_baseline(baseline_data)
    return baseline_data


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect baseline pose data from images')
    parser.add_argument('--folder', '-f', type=str, 
                        default=os.path.join(os.path.dirname(__file__), 'testing_images'),
                        help='Path to folder containing baseline images')
    parser.add_argument('--output', '-o', type=str, 
                        default=None,
                        help='Path to save baseline JSON file')
    parser.add_argument('--method', '-m', type=str, 
                        choices=['average', 'median', 'first', 'all'],
                        default='average',
                        help='Aggregation method for multiple images')
    
    args = parser.parse_args()
    
    print(f"Collecting baseline from: {args.folder}")
    print(f"Aggregation method: {args.method}")
    
    baseline = collect_baseline_from_folder(
        args.folder, 
        args.output, 
        args.method
    )
    
    print("\nBaseline Summary:")
    print(f"  Images processed: {baseline['metadata']['num_images_processed']}")
    print(f"  Files: {baseline['metadata']['processed_files']}")
