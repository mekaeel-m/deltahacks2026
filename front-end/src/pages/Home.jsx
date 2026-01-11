import Navbar from "../components/Navbar.jsx";
import Webcam from "../components/Webcam.jsx";
import { useRef, useState, useEffect } from "react";
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

    useEffect(() => {
        const container = document.querySelector('.scroll-container');
        if (!container) return;
        let timeout;
        const handleScroll = () => {
            container.classList.add('smooth-scroll');
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                container.classList.remove('smooth-scroll');
            }, 900); // duration matches transition
        };
        container.addEventListener('wheel', handleScroll, { passive: true });
        return () => {
            container.removeEventListener('wheel', handleScroll);
            clearTimeout(timeout);
        };
    }, []);

    return (
        <div className="scroll-container">
            <section className="snap-section">
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
            </section>

            <section className="snap-section" id="pose-detection-section" ref={webcamSectionRef}>
                <div className="webcam-section">
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
            </section>
        </div>
    )
}