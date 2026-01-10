import { useEffect, useRef, useState, forwardRef } from "react";
import io from "socket.io-client";
import "../styles/Webcam.css";

const SOCKET_SERVER_URL = "http://localhost:5001"; // Flask backend

const Webcam = forwardRef((props, ref) => {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const canvasRef = useRef(null);
  const socketRef = useRef(null);
  const intervalRef = useRef(null);

  const [isActive, setIsActive] = useState(false);
  const [processedImg, setProcessedImg] = useState(null);

  /* =======================
     Webcam control
  ======================= */

  const startWebcam = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: true,
      audio: false,
    });

    streamRef.current = stream;
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
    }

    connectSocket();
    startFrameCapture();

    setIsActive(true);
  };

  const stopWebcam = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    if (socketRef.current) {
      socketRef.current.disconnect();
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsActive(false);
  };

  /* =======================
     Socket logic
  ======================= */

  const connectSocket = () => {
    socketRef.current = io(SOCKET_SERVER_URL);

    socketRef.current.on("connect", () => {
      console.log("Connected to backend");
    });

    socketRef.current.on("processed_frame", (data) => {
      setProcessedImg(data);
    });
  };

  /* =======================
     Frame capture logic
  ======================= */

  const startFrameCapture = () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;

    intervalRef.current = setInterval(() => {
      if (!video || video.videoWidth === 0) return;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const frame = canvas.toDataURL("image/jpeg");

      if (socketRef.current) {
        socketRef.current.emit("video_frame", frame);
      }
    }, 200); // ~10 FPS
  };

  /* =======================
     Cleanup
  ======================= */

  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, []);

  /* =======================
     Expose API to parent
  ======================= */

  if (ref) {
    ref.current = { startWebcam, stopWebcam };
  }

  /* =======================
     Render
  ======================= */

  return (
    <div className="webcam-card">
      <div className="card-header card-header-flex">
        <div>
          <h2 className="card-title">Pose Detection</h2>
          <p className="card-description">
            Start the camera to analyze your posture in real-time
          </p>
        </div>
        <div className="card-header-action">
          {!isActive ? (
            <div className="action-button-wrapper">
              <button 
                onClick={props.onStartCamera}
                className="action-button-inner"
              >
                Start Camera
              </button>
            </div>
          ) : (
            <div className="action-button-wrapper stop">
              <button 
                onClick={props.onStopCamera}
                className="action-button-inner"
              >
                Stop Camera
              </button>
            </div>
          )}
        </div>
      </div>
      <div className="card-content">
        <div className="video-container">
          <video ref={videoRef} autoPlay playsInline />
          {!isActive && (
            <div className="webcam-off-message">
              Camera is off
            </div>
          )}
        </div>

        {processedImg && (
          <img
            src={processedImg}
            alt="Processed"
            className="processed-frame"
          />
        )}
      </div>

      {/* Hidden canvas for frame capture */}
      <canvas ref={canvasRef} style={{ display: "none" }} />
    </div>
  );
});

Webcam.displayName = "Webcam";
export default Webcam;
