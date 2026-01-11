import React, { useRef, useEffect, useState } from 'react';
import Webcam from 'react-webcam';
import io from 'socket.io-client';

const SOCKET_SERVER_URL = 'http://localhost:5000';  // Change for production

const WebcamStream = () => {
  const webcamRef = useRef(null);
  const socketRef = useRef(null);
  const [processedImg, setProcessedImg] = useState(null);  // For displaying processed frame

  useEffect(() => {
    // Connect to Socket.IO server
    socketRef.current = io(SOCKET_SERVER_URL);

    socketRef.current.on('connect', () => {
      console.log('Connected to backend');
    });

    // Optional: Receive processed frame
    socketRef.current.on('processed_frame', (data) => {
      setProcessedImg(data);
    });

    // Capture and send frames every ~100ms (10 FPS; adjust as needed)
    const interval = setInterval(() => {
      if (webcamRef.current) {
        const screenshot = webcamRef.current.getScreenshot();  // Returns base64 JPEG data URL
        if (screenshot) {
          socketRef.current.emit('video_frame', screenshot);
        }
      }
      // Adjust interval time for desired FPS
    }, 50);

    return () => {
      clearInterval(interval);
      socketRef.current.disconnect();
    };
  }, []);

  return (
    <div style={{ textAlign: 'center' }}>
      <h1>Live Webcam Stream to Flask</h1>
      <Webcam
        audio={false}
        ref={webcamRef}
        screenshotFormat="image/jpeg"
        videoConstraints={{ facingMode: 'user' }}
        style={{ width: '640px', height: '480px' }}
      />
      <div>
        <h2>Original Feed (above) → Processed Feed (below)</h2>
        {processedImg && (
          <img src={processedImg} alt="Processed" style={{ width: '640px', height: '480px' }} />
        )}
      </div>
    </div>
  );
};

export default WebcamStream;