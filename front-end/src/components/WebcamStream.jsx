import React, { useRef, useEffect, useState } from 'react';
import Webcam from 'react-webcam';
import io from 'socket.io-client';

const SOCKET_SERVER_URL = 'http://localhost:5001';  // Change for production
  // NOTE: need 5001 for percent due to FLASK API 

const WebcamStream = () => {
  const webcamRef = useRef(null);
  const socketRef = useRef(null);
  const [processedImg, setProcessedImg] = useState(null);  // For displaying processed frame

  const [score,setScore] = useState(null);
  const [error,setError] = useState(null);
  const [loading,setLoading] = useState(null);

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
    const interval = setInterval(async() => {
      if (webcamRef.current) {
        try {
          const screenshot = webcamRef.current.getScreenshot(); 
          if(screenshot) {
            setLoading(true);

            const response = await fetch(`${SOCKET_SERVER_URL}/score`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              }, 
              body: JSON.stringify({
                image: screenshot
              })
            });

            if (!response.ok) {
              const data = await response.json();
              setError(data.error || 'Failed to get score'); 
              setScore(null);
            } else {
              const data = await response.json();
              setScore(data.score); 
              setError(null); 
            }
        }
      } catch (err) {
        setError('Connection error: ' + err.message);
        setScore(null);
      } finally {
        setLoading(false);
      }
    }
    }, 150);

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
      <div style={{ marginTop: '20px'}}>
        {error && (
          <div style={{color: 'red', fontSize: '16px', marginBottom: '10px'}}>
            Error: {error}
          </div>
        )}
        { score !== null && (
          <div style={{
            fontSize: '32px', 
            fontWeight: 'bold', 
            color: score >= 75 ? '#00aa00' : score >= 50 ? '#ff8800' : '#ff0000', 
            marginBottom: '10px'
          }}>
            Score: {score}%
          </div>
        )}
        {
          loading && score === null && !error && (
            <div style={{ color: '#666', fontSize: '14px'}}>
              Loading...
            </div>
        )}
        { !loading && score === null && !error && (
          <div style={{ color: '#666', fontSize: '14px'}}>
            Waiting for pose detection...
          </div>
        ) }

      </div>
    </div>
  );
};

export default WebcamStream;