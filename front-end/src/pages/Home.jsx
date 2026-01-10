import Navbar from "../components/Navbar.jsx";
import Webcam from "../components/Webcam.jsx";
import "../styles/Home.css";


export default function Home() {
    return (
        <>
            <Navbar/>
            <div className="hero">
                <div className="left-content">
                    <h1 className="title">Violina</h1>
                    <div className="webcam-box">
                        <Webcam/>
                    </div>
                </div>
                <div className="right-content">
                    <p className="description">
                        Practice with better posture, effortlessly.
                    </p>
                    <p className="subdescription">
                        Violina watches your playing and gently lets you know when your form slips, so you can stay focused on the music while improving naturally.
                    </p>
                </div>
            </div>
        </>
    )
}