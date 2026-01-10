import Navbar from "../components/Navbar.jsx";
import Webcam from "../components/Webcam.jsx";
import { useRef, useState } from "react";
import "../styles/Home.css";


export default function Home() {
    const [isWebcamActive, setIsWebcamActive] = useState(false);
    const webcamRef = useRef(null);

    const handleStartWebcam = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 1280 }, height: { ideal: 720 } },
                audio: false,
            });
            if (webcamRef.current) {
                webcamRef.current.startWebcam(stream);
                setIsWebcamActive(true);
            }
        } catch (error) {
            console.error('Error accessing webcam:', error);
            alert('Unable to access webcam. Please check permissions.');
        }
    };

    const handleStopWebcam = () => {
        if (webcamRef.current) {
            webcamRef.current.stopWebcam();
            setIsWebcamActive(false);
        }
    };

    return (
        <>
            <Navbar/>
            <div className="hero">
                <div className="left-content">
                    <h1 className="title">Violina</h1>
                    <div className="webcam-box">
                        <Webcam ref={webcamRef}/>
                    </div>
                </div>
                <div className="right-content">
                    <p className="description">
                        Practice with better posture, effortlessly.
                    </p>
                    <p className="subdescription">
                        Violina watches your playing and gently lets you know when your form slips, so you can stay focused on the music while improving naturally.
                    </p>
                    {!isWebcamActive ? (
                        <button 
                            onClick={handleStartWebcam}
                            className="action-button"
                        >
                            Start Webcam
                        </button>
                    ) : (
                        <button 
                            onClick={handleStopWebcam}
                            className="action-button stop"
                        >
                            Stop Webcam
                        </button>
                    )}
                </div>
            </div>
        </>
    )
}