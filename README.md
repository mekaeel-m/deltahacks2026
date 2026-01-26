# Violina - Real-Time ML Violin Posture Tracker

## Inspiration
Violin posture often breaks down not because players don't know proper form, but because fatigue sets in during practice. As focus shifts to the music, wrists drop, arms drift, and tension builds without the player noticing. Violina was created to make posture visible again — providing real-time awareness when a teacher isn't there to correct it. We wanted to empower musicians to self-correct and build healthy habits, even when practicing alone.

## What It Does
Violina is a real-time ML violin posture tracker that uses a webcam to analyze wrist positioning, arm angles, and joint alignment while a player performs. It detects posture drift and provides immediate visual feedback to help players correct form before bad habits develop. The system highlights incorrect posture, offers suggestions for improvement, and tracks changes over the course of a practice session.

## How We Built It
Violina uses a live webcam feed on the frontend, built with React, and streams frames to a backend optimized for low latency using Flask. On the backend, MediaPipe pose and hand landmark detection extract joint positions, which are analyzed using geometric calculations to evaluate posture. The backend processes each frame, compares the player's form to a baseline, and returns feedback in real time with visual overlays and alerts. We designed the architecture to be modular, allowing for easy integration of new features and models.

## Challenges We Ran Into
Running multiple computer vision models in real time introduced performance and latency challenges. We had to balance accuracy with responsiveness while translating expressive human movement into measurable geometry. Ensuring reliable detection across different lighting conditions, camera angles, and player physiques required extensive tuning and testing. Integrating the feedback loop seamlessly into the user interface was also a key challenge.

## What's Next for Violina
We plan to expand Violina beyond posture into context-aware feedback by integrating music and note analysis. Future versions could analyze bowing technique, vibrato, and finger placement. Long term, Violina could track progress over time, generate personalized reports, and adapt feedback to each player's unique technique and physiology. We also aim to support other instruments and group practice scenarios.

## Built With
- Flask (backend server)
- Python (ML and data processing)
- MediaPipe (pose and hand landmark detection)
- React (frontend UI)
- Machine Learning (posture analysis)

## Getting Started
1. Clone the repository.
2. Install backend dependencies from `back-end/requirements.txt`.
3. Start the backend servers (Flask).
```
python back-end/correctForm.py
```
```
python back-end/webcam.py
```
4. Run the frontend (React) from `front-end/`.
```
npm run dev
```
5. Connect your webcam and begin a session.

## License
This project is licensed under the MIT License.