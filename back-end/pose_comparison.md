# Pose Comparison System

This system allows you to collect baseline pose data from reference images and compare new poses against that baseline in real-time.

## Overview

The system consists of three main modules:

1. **`baseline_collector.py`** - Collects and aggregates pose data from baseline images
2. **`pose_comparator.py`** - Compares new poses against the baseline
3. **`correctForm.py`** - Flask server with endpoints for real-time comparison

## Quick Start

### 1. Collect Baseline Data

Place your reference images (showing correct form) in the `testing_images/` folder, then run:

```bash
python run_baseline_collection.py
```

This will:
- Process all images in the folder
- Extract pose landmarks from each image
- Calculate joint angles (elbow, shoulder)
- Average the data across all images
- Save to `output/baseline_data.json`

### 2. Start the Server

**Option A: Use the main detection server (port 5000)**
```bash
python drawingLines.py
```

**Option B: Use the dedicated form correction server (port 5001)**
```bash
python correctForm.py
```

### 3. Compare Poses

Send images to the `/compare-pose` endpoint:

```bash
# Using curl with file upload
curl -X POST -F "image=@your_image.jpg" http://localhost:5000/compare-pose

# Using curl with base64 JSON
curl -X POST -H "Content-Type: application/json" \
  -d '{"image": "base64_encoded_image_data"}' \
  http://localhost:5000/compare-pose
```

## API Endpoints

### Main Server (drawingLines.py - port 5000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/detect-arms` | POST | Detect arms, return base64 image |
| `/detect-arms-raw` | POST | Detect arms, return raw image |
| `/landmarks-only` | POST | Return only landmark coordinates |
| `/compare-pose` | POST | Compare pose against baseline |
| `/baseline-status` | GET | Check if baseline is loaded |

### Form Correction Server (correctForm.py - port 5001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with baseline status |
| `/collect-baseline` | POST | Collect baseline from folder |
| `/set-baseline` | POST | Set baseline from single image |
| `/get-baseline` | GET | Get current baseline data |
| `/compare-pose` | POST | Compare pose, return accuracy flag |
| `/compare-pose-visual` | POST | Compare pose with visual overlay |
| `/configure` | POST | Configure comparison thresholds |

## Response Format

### Compare Pose Response

```json
{
  "success": true,
  "flag": {
    "is_accurate": true,
    "accuracy_percentage": 87.5,
    "accuracy_level": "good",
    "message": "Great form! Accuracy: 87.5%",
    "needs_correction": false,
    "corrections": []
  },
  "detailed_feedback": {
    "joint_feedback": [
      {
        "joint": "shoulder",
        "arm": "left_arm",
        "deviation": 0.023,
        "is_accurate": true,
        "message": "Shoulder position is correct"
      }
    ],
    "angle_feedback": {
      "left_arm": {
        "elbow_angle": {
          "baseline": 145.2,
          "current": 142.8,
          "deviation": 2.4,
          "is_accurate": true,
          "message": "Elbow angle is correct"
        }
      }
    }
  }
}
```

## Accuracy Levels

| Level | Accuracy % | Description |
|-------|------------|-------------|
| `excellent` | ≥90% | Perfect or near-perfect form |
| `good` | ≥75% | Good form, minor adjustments |
| `fair` | ≥50% | Needs improvement |
| `poor` | <50% | Significant corrections needed |

## Configuration

You can adjust comparison thresholds via the `/configure` endpoint:

```json
{
  "position_threshold": 0.1,    // Max normalized position deviation (0-1)
  "angle_threshold": 15.0,      // Max angle deviation in degrees
  "accuracy_threshold": 75.0    // Min % to be considered "accurate"
}
```

## Programmatic Usage

```python
from baseline_collector import collect_baseline_from_folder
from pose_comparator import compare_pose_to_baseline
import cv2

# Step 1: Collect baseline (run once)
baseline = collect_baseline_from_folder(
    'path/to/baseline/images',
    'output/baseline_data.json',
    aggregate_method='average'
)

# Step 2: Compare new images
image = cv2.imread('new_pose.jpg')
result = compare_pose_to_baseline(image, 'output/baseline_data.json')

print(f"Accurate: {result['flag']['is_accurate']}")
print(f"Accuracy: {result['flag']['accuracy_percentage']}%")
print(f"Message: {result['flag']['message']}")
```

## How It Works

### Baseline Collection
1. Reads all images from the specified folder
2. Detects pose landmarks using MediaPipe
3. Normalizes coordinates to 0-1 range (scale-invariant)
4. Calculates joint angles (elbow bend, shoulder position)
5. Aggregates data using average/median across all images
6. Stores standard deviation for adaptive thresholds

### Pose Comparison
1. Detects pose in the input image
2. Normalizes coordinates to match baseline scale
3. Calculates position deviation for each joint
4. Calculates angle deviation for elbow and shoulder
5. Scores each joint/angle based on deviation from baseline
6. Computes overall accuracy percentage
7. Generates human-readable feedback messages

### Visual Overlay
- **Cyan dashed lines**: Baseline pose (where you should be)
- **Green solid lines**: Current pose (correct)
- **Orange solid lines**: Current pose (fair accuracy)
- **Red solid lines**: Current pose (needs correction)
- **Green dots**: Joints in correct position
- **Red dots**: Joints needing adjustment

## Tips for Best Results

1. **Consistent camera angle**: Use similar camera angles for baseline and comparison images
2. **Good lighting**: Ensure subjects are well-lit for accurate detection
3. **Multiple baseline images**: Use 5-10 images for more robust baseline
4. **Adjust thresholds**: Loosen thresholds for beginners, tighten for advanced users
5. **Use median aggregation**: More robust to outliers than average
