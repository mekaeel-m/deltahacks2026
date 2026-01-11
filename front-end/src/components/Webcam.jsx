import { useEffect, useRef, useState, forwardRef } from 'react';
import '../styles/Webcam.css';

const Webcam = forwardRef((props, ref) => {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [isActive, setIsActive] = useState(false);

  const startWebcam = (stream) => {
    streamRef.current = stream;
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
    }
    setIsActive(true);
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

  // Expose methods to parent component
  if (ref) {
    ref.current = { startWebcam, stopWebcam };
  }

  return (
    <div className="webcam-card">
      <div className="card-header">
        <h2 className="card-title">Pose Detection</h2>
        <p className="card-description">
          Start the camera to analyze your posture in real-time
        </p>
      </div>

      <div className="card-content">
        <div className="video-container">
          <video
            ref={videoRef}
            autoPlay
            playsInline
          />
          {!isActive && (
            <div className="webcam-off-message">
              Camera is off
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

Webcam.displayName = 'Webcam';
export default Webcam;
