import Navbar from "../components/Navbar.jsx";
import Webcam from "../components/Webcam.jsx";
import { useRef, useState } from "react";
import "../styles/Home.css";
import "../styles/animButton.css";


export default function Home() {
    const [isWebcamActive, setIsWebcamActive] = useState(false);
    const webcamRef = useRef(null);
    const webcamSectionRef = useRef(null);

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
            console.error('Error accessing camera:', error);
            alert('Unable to access camera. Please check permissions.');
        }
    };

    const handleStopWebcam = () => {
        if (webcamRef.current) {
            webcamRef.current.stopWebcam();
            setIsWebcamActive(false);
        }
    };

    const handleGetStarted = () => {
        webcamSectionRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    return (
        <>
            <Navbar/>
            <div className="hero">
                <div className="left-content">
                    <h1 className="title">Violina</h1>
                    <p className="description">
                        Practice with better posture, effortlessly.
                    </p>
                    <p className="subdescription">
                        Violina watches your playing and gently lets you know when your form slips, so you can stay focused on the music while improving naturally.
                    </p>
                    <div className="action-button-wrapper">
                        <button 
                            onClick={handleGetStarted}
                            className="action-button-inner"
                        >
                            Get Started
                        </button>
                    </div>
                </div>
            </div>

            <div className="webcam-section" ref={webcamSectionRef}>
                <div className="webcam-left">
                    <div className="webcam-box">
                        <Webcam 
                          ref={webcamRef}
                          onStartCamera={handleStartWebcam}
                          onStopCamera={handleStopWebcam}
                        />
                    </div>
                </div>
                <div className="webcam-right">
                    <div className="settings-panel">
                        <h2 className="settings-title">Settings</h2>
                    </div>
                </div>
            </div>
        </>
    )
}