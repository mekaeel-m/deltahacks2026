# Arm Detection Flask API

A Flask application that detects human arms in images and draws lines from shoulder → elbow → wrist → forefinger using MediaPipe.

## Features

- **Efficient pose detection** using MediaPipe Pose and Hands models
- **Works from various camera angles** (optimized for chest-height cameras)
- **Detects both arms** simultaneously
- **Draws connected lines**: shoulder → elbow → wrist → forefinger
- **Multiple input formats**: Base64 JSON or file upload
- **Multiple output formats**: Base64 image, raw image, or landmarks only

## Installation

```bash
cd back-end
pip install -r requirements.txt
```

## Running the Server

```bash
python drawingLines.py
```

The server will start on `http://localhost:5000` by default.

### Environment Variables

- `PORT`: Server port (default: 5000)
- `FLASK_DEBUG`: Enable debug mode (default: False)

## API Endpoints

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Arm detection service is running"
}
```

### POST /detect-arms
Detect arms in an image and return the processed image with arm lines drawn.

**Request (JSON):**
```json
{
  "image": "base64_encoded_image_string"
}
```

**Request (Form Data):**
- Field: `image` (file)

**Response:**
```json
{
  "success": true,
  "processed_image": "data:image/png;base64,...",
  "detection_result": {
    "arms_detected": true,
    "pose_detected": true,
    "hands_detected": true,
    "num_hands": 2,
    "landmarks": {
      "left_arm": {
        "shoulder": {"x": 100, "y": 150, "visibility": 0.95},
        "elbow": {"x": 120, "y": 250, "visibility": 0.92},
        "wrist": {"x": 140, "y": 350, "visibility": 0.88}
      },
      "right_arm": {
        "shoulder": {"x": 300, "y": 150, "visibility": 0.94},
        "elbow": {"x": 280, "y": 250, "visibility": 0.91},
        "wrist": {"x": 260, "y": 350, "visibility": 0.87}
      }
    }
  }
}
```

### POST /detect-arms-raw
Detect arms and return the processed image directly as PNG.

**Request (Form Data):**
- Field: `image` (file)

**Response:** PNG image file

### POST /landmarks-only
Detect arms and return only the landmark coordinates (no image processing).

**Request:** Same as `/detect-arms`

**Response:**
```json
{
  "success": true,
  "detection_result": {
    "arms_detected": true,
    "pose_detected": true,
    "hands_detected": true,
    "num_hands": 2,
    "landmarks": {...}
  }
}
```

## How It Works

### MediaPipe Pose Landmarks Used

| Body Part | Landmark Index |
|-----------|----------------|
| Left Shoulder | 11 |
| Left Elbow | 13 |
| Left Wrist | 15 |
| Right Shoulder | 12 |
| Right Elbow | 14 |
| Right Wrist | 16 |

### MediaPipe Hand Landmarks Used

| Finger Part | Landmark Index |
|-------------|----------------|
| Wrist | 0 |
| Index Finger Tip | 8 |

### Detection Process

1. **Pose Detection**: MediaPipe Pose detects the full body pose and extracts shoulder, elbow, and wrist positions
2. **Hand Detection**: MediaPipe Hands detects hands and extracts finger positions
3. **Hand-Wrist Matching**: The algorithm matches detected hands to the corresponding arm by comparing wrist positions
4. **Line Drawing**: Lines are drawn connecting:
   - Shoulder → Elbow (green line)
   - Elbow → Wrist (green line)
   - Wrist → Index Finger Tip (green line)
5. **Joint Markers**: Red circles are drawn at each joint point

### Visibility Threshold

Landmarks are only used if their visibility score is above 0.5 (50%). This ensures accurate detection even when parts of the arm are partially occluded.

## Example Usage

### Python (requests library)

```python
import requests
import base64

# Using file upload
with open('image.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/detect-arms',
        files={'image': f}
    )
    result = response.json()

# Using base64
with open('image.jpg', 'rb') as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

response = requests.post(
    'http://localhost:5000/detect-arms',
    json={'image': image_base64}
)
result = response.json()
```

### JavaScript (fetch)

```javascript
// Using file upload
const formData = new FormData();
formData.append('image', fileInput.files[0]);

const response = await fetch('http://localhost:5000/detect-arms', {
    method: 'POST',
    body: formData
});
const result = await response.json();

// Using base64
const response = await fetch('http://localhost:5000/detect-arms', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image: base64ImageString })
});
const result = await response.json();
```

### cURL

```bash
# File upload
curl -X POST -F "image=@photo.jpg" http://localhost:5000/detect-arms

# Get raw image
curl -X POST -F "image=@photo.jpg" http://localhost:5000/detect-arms-raw -o output.png
```

## Configuration

### Line Appearance

In `drawingLines.py`, you can customize:

```python
ARM_LINE_COLOR = (0, 255, 0)  # Green (BGR format)
ARM_LINE_THICKNESS = 3
POINT_COLOR = (0, 0, 255)    # Red (BGR format)
POINT_RADIUS = 5
```

### Model Complexity

The pose model complexity can be adjusted (0=lite, 1=full, 2=heavy):

```python
mp_pose.Pose(
    model_complexity=1,  # Change this value
    ...
)
```

- `0` (Lite): Fastest, less accurate
- `1` (Full): Balanced (default)
- `2` (Heavy): Most accurate, slower

## Troubleshooting

### Arms not detected
- Ensure the person's arms are visible in the frame
- Check that lighting is adequate
- Try adjusting the `min_detection_confidence` parameter

### Forefinger not connected
- The hand must be clearly visible
- Ensure the hand is not too far from the wrist position detected by pose
- The matching threshold is 10% of the image diagonal

### Performance issues
- Use `model_complexity=0` for faster processing
- Reduce image resolution before sending to the API
- Consider using GPU acceleration with MediaPipe
