import { useEffect, useRef, useState, forwardRef } from "react";
import io from "socket.io-client";
import "../styles/Webcam.css";

const SOCKET_SERVER_URL = "http://localhost:5001"; // Flask webcam.py for video overlay
const SCORE_SERVER_URL = "http://localhost:5002";   // Flask correctForm.py for accuracy scores

const Webcam = forwardRef((props, ref) => {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const canvasRef = useRef(null);
  const socketRef = useRef(null);
  const frameRequestRef = useRef(null);
  const waitingRef = useRef(false); // backpressure: only one in-flight frame

  const [processedImg, setProcessedImg] = useState(null);
  const [loading, setLoading] = useState(false);

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

    props.setIsActive(true);
  };

  const stopWebcam = () => {
    if (frameRequestRef.current) {
      cancelAnimationFrame(frameRequestRef.current);
      frameRequestRef.current = null;
    }

    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    waitingRef.current = false;
    setProcessedImg(null);
    props.setIsActive(false);
  };

  /* =======================
     Socket logic
  ======================= */

  const connectSocket = () => {
    socketRef.current = io(SOCKET_SERVER_URL);

    socketRef.current.on("connect", () => {
      console.log("Connected to backend");
    });

    socketRef.current.on("pose_analysis", (data) => {
      console.debug("received pose_analysis");

      if (data.processed_image) {
        setProcessedImg(data.processed_image);
      }

      if (data.error) {
        props.setError(data.error);
        props.setScore(null);
        props.setJoints({});
      } else {
        props.setError(null);
        props.setScore(data.score ?? null);
        props.setJoints(data.joints || {});
      }

      // Release backpressure
      waitingRef.current = false;
    });
  };

  /* =======================
     Frame capture logic
  ======================= */

  const startFrameCapture = () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    const MAX_WIDTH = 960; // cap width to reduce payload
    const JPEG_QUALITY = 0.6; // reduce JPEG quality for smaller payloads

    const frameLoop = () => {
      // schedule next frame
      frameRequestRef.current = requestAnimationFrame(frameLoop);

      if (!video || video.videoWidth === 0) return;

      // if a frame is already in-flight, skip sending a new one
      if (waitingRef.current) return;

      // compute scaled dimensions preserving aspect
      const scale = Math.min(1, MAX_WIDTH / video.videoWidth);
      const targetWidth = Math.round(video.videoWidth * scale);
      const targetHeight = Math.round(video.videoHeight * scale);

      canvas.width = targetWidth;
      canvas.height = targetHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, targetWidth, targetHeight);

      // get compressed dataURL directly (base64) to keep backend logic unchanged
      try {
        const dataUrl = canvas.toDataURL("image/jpeg", JPEG_QUALITY);
        if (socketRef.current && socketRef.current.connected) {
          // set waiting flag until server responds
          waitingRef.current = true;
          try {
            const b64 = dataUrl.split(",")[1] || "";
            console.debug("emit video_frame: bytes=", Math.round((b64.length * 3) / 4));
          } catch (e) {}
          
          // Send to webcam.py via Socket.IO (for processed overlay)
          socketRef.current.emit("video_frame", dataUrl);
          
          // ALSO send to correctForm.py via HTTP POST (for accuracy score)
          // sendFrameForScore(dataUrl);
        }
      } catch (e) {
        // ignore and continue
      }
    };

    // start loop
    frameRequestRef.current = requestAnimationFrame(frameLoop);
  };

  // Send frame to correctForm.py to get accuracy score with joint details
  // const sendFrameForScore = async (dataUrl) => {
  //   try {
  //     const response = await fetch(`${SCORE_SERVER_URL}/score-detailed`, {
  //       method: 'POST',
  //       headers: {
  //         'Content-Type': 'application/json',
  //       },
  //       body: JSON.stringify({
  //         image: dataUrl
  //       })
  //     });

  //     if (!response.ok) {
  //       const data = await response.json();
  //       props.setError(data.error || 'Failed to get score');
  //       props.setScore(null);
  //       props.setJoints({});
  //     } else {
  //       const data = await response.json();
  //       props.setScore(data.score);
  //       props.setJoints(data.joints || {});
  //       props.setError(null);
  //     }
  //   } catch (err) {
  //     props.setError('Score service unavailable');
  //     props.setScore(null);
  //     props.setJoints({});
  //   }
  // };

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
          {!props.isActive ? (
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
      <video ref={videoRef} style={{opacity:0, width:0, height:0, position:'absolute'}} autoPlay playsInline />
      <div className="card-content">
        <div className="video-container">
          {!props.isActive && (
            <div className="webcam-off-message">
              Camera is off
            </div>
          )}
          {props.isActive && processedImg && (
            <img
              src={processedImg}
              alt="Processed"
              className="processed-frame"
            />
          )}
        </div>
      </div>
        
      {/* Hidden canvas for frame capture */}
      <canvas ref={canvasRef} style={{ display: "none" }} />
    </div>
  );
});

Webcam.displayName = "Webcam";
export default Webcam;
