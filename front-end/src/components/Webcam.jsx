import { useEffect, useRef, forwardRef } from 'react';
import '../styles/Webcam.css';

const Webcam = forwardRef((props, ref) => {
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const startWebcam = (stream) => {
    streamRef.current = stream;
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
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
          Start the webcam to analyze your posture in real-time
        </p>
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
});

Webcam.displayName = 'Webcam';
export default Webcam;
