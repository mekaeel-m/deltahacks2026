import Navbar from "../components/Navbar.jsx";
import Webcam from "../components/Webcam.jsx";
import { useRef, useState, useEffect } from "react";
import "../styles/Home.css";
import "../styles/animButton.css";


export default function Home() {
    const [isWebcamActive, setIsWebcamActive] = useState(false);
    const webcamRef = useRef(null);
    const webcamSectionRef = useRef(null);

    const [score, setScore] = useState(null);
    const [error, setError] = useState(null);
    const [isActive, setIsActive] = useState(false);
    const [joints, setJoints] = useState({});

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
                              setScore={setScore} // need to set score via webcam input
                              setError={setError}
                              isActive={isActive}
                              setIsActive={setIsActive}
                              joints={joints}
                              setJoints={setJoints}
                            />
                        </div>
                    </div>
                    <div className="webcam-right">
                        <div className="settings-panel">
                            <h2 className="settings-title">Settings</h2>


                                {/* Overall Score Display */}
                                {score !== null && (
                                <div style={{
                                    marginTop: '15px',
                                    padding: '12px',
                                    textAlign: 'center',
                                    backgroundColor: score >= 75 ? '#e8f5e9' : score >= 50 ? '#fff3e0' : '#ffebee',
                                    borderRadius: '8px'
                                }}>
                                    <div style={{
                                    fontSize: '28px',
                                    fontWeight: 'bold',
                                    color: score >= 75 ? '#2e7d32' : score >= 50 ? '#e65100' : '#c62828'
                                    }}>
                                    {score}%
                                    </div>
                                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                                    Overall Accuracy
                                    </div>
                                </div>
                                )}
                                
                                {/* Joint Feedback Display */}
                                {Object.keys(joints).length > 0 && (
                                <div style={{ marginTop: '15px', padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
                                    <h4 style={{ margin: '0 0 12px 0', fontSize: '13px', fontWeight: 'bold', color: '#333' }}>
                                    Joint Accuracy:
                                    </h4>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                                    {/* Left Arm Column */}
                                    <div>
                                        {Object.entries(joints)
                                        .filter(([_, joint]) => joint.arm === 'left_arm')
                                        .map(([key, joint]) => (
                                            <div 
                                            key={key}
                                            style={{
                                                padding: '10px',
                                                borderRadius: '6px',
                                                backgroundColor: joint.is_accurate ? '#e8f5e9' : '#ffebee',
                                                border: `2px solid ${joint.is_accurate ? '#4caf50' : '#f44336'}`,
                                                fontSize: '12px',
                                                marginBottom: '8px'
                                            }}
                                            >
                                            <div style={{ 
                                                fontWeight: 'bold', 
                                                color: joint.is_accurate ? '#2e7d32' : '#c62828',
                                                marginBottom: '4px',
                                                textTransform: 'capitalize'
                                            }}>
                                                L {joint.joint}
                                            </div>
                                            <div style={{ fontSize: '11px', color: '#555' }}>
                                                {joint.is_accurate ? '✓ Good' : '✗ Off'}
                                            </div>
                                            <div style={{ fontSize: '10px', color: '#888', marginTop: '3px' }}>
                                                Dev: {(joint.deviation * 100).toFixed(0)}%
                                            </div>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Right Arm Column */}
                                    <div>
                                        {Object.entries(joints)
                                        .filter(([_, joint]) => joint.arm === 'right_arm')
                                        .map(([key, joint]) => (
                                            <div 
                                            key={key}
                                            style={{
                                                padding: '10px',
                                                borderRadius: '6px',
                                                backgroundColor: joint.is_accurate ? '#e8f5e9' : '#ffebee',
                                                border: `2px solid ${joint.is_accurate ? '#4caf50' : '#f44336'}`,
                                                fontSize: '12px',
                                                marginBottom: '8px'
                                            }}
                                            >
                                            <div style={{ 
                                                fontWeight: 'bold', 
                                                color: joint.is_accurate ? '#2e7d32' : '#c62828',
                                                marginBottom: '4px',
                                                textTransform: 'capitalize'
                                            }}>
                                                R {joint.joint}
                                            </div>
                                            <div style={{ fontSize: '11px', color: '#555' }}>
                                                {joint.is_accurate ? '✓ Good' : '✗ Off'}
                                            </div>
                                            <div style={{ fontSize: '10px', color: '#888', marginTop: '3px' }}>
                                                Dev: {(joint.deviation * 100).toFixed(0)}%
                                            </div>
                                            </div>
                                        ))}
                                    </div>
                                    </div>
                                </div>
                                )}
                                
                                {/* Error Display */}
                                {error && (
                                <div style={{
                                    marginTop: '10px',
                                    padding: '10px',
                                    backgroundColor: '#ffebee',
                                    border: '1px solid #f44336',
                                    borderRadius: '4px',
                                    color: '#c62828',
                                    fontSize: '12px'
                                }}>
                                    {error}
                                </div>
                                )}
                        </div>
                    </div>
                </div>
            </section>
        </div>
    )
}