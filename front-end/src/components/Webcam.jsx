import { useEffect, useRef, useState } from 'react';
import '../styles/Webcam.css';

export default function Webcam() {
  const videoRef = useRef(null);
  const [isActive, setIsActive] = useState(false);
  const streamRef = useRef(null);

  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsActive(true);
    } catch (error) {
      console.error('Error accessing webcam:', error);
      alert('Unable to access webcam. Please check permissions.');
    }
  };

  const stopWebcam = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsActive(false);
  };

  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, []);

  return (
    <div className="webcam-card">
      <div className="card-header">
        <h2 className="card-title">Pose Detection</h2>
        <p className="card-description">
          Start the webcam to analyze your posture in real-time
        </p>
        {!isActive ? (
          <button
            onClick={startWebcam}
            className="webcam-button start-button"
          >
            Start Webcam
          </button>
        ) : (
          <button
            onClick={stopWebcam}
            className="webcam-button stop-button"
          >
            Stop Webcam
          </button>
        )}
      </div>

      <div className="card-content">
        <div className="video-container">
          <video
            ref={videoRef}
            autoPlay
            playsInline
          />
        </div>
      </div>
    </div>
  );
}
