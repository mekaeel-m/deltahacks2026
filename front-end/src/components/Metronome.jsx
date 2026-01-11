import { useState, useEffect, useRef } from "react";
import "../styles/Metronome.css";

const TIME_SIGNATURES = [
    { beats: 2, label: "2/4" },
    { beats: 3, label: "3/4" },
    { beats: 4, label: "4/4" },
    { beats: 6, label: "6/8" },
];

export default function Metronome() {
    const [bpm, setBpm] = useState(120);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentBeat, setCurrentBeat] = useState(0);
    const [timeSignature, setTimeSignature] = useState(TIME_SIGNATURES[2]); // 4/4 default
    
    const audioContextRef = useRef(null);
    const intervalRef = useRef(null);
    const nextNoteTimeRef = useRef(0);
    const currentBeatRef = useRef(0);

    const createClick = (isAccent = false) => {
        if (!audioContextRef.current) return;
        
        const osc = audioContextRef.current.createOscillator();
        const gain = audioContextRef.current.createGain();
        
        osc.connect(gain);
        gain.connect(audioContextRef.current.destination);
        
        osc.frequency.value = isAccent ? 1000 : 800;
        gain.gain.value = isAccent ? 0.3 : 0.2;
        
        const time = audioContextRef.current.currentTime;
        osc.start(time);
        gain.gain.exponentialRampToValueAtTime(0.001, time + 0.1);
        osc.stop(time + 0.1);
    };

    const scheduler = () => {
        while (nextNoteTimeRef.current < audioContextRef.current.currentTime + 0.1) {
            const isAccent = currentBeatRef.current === 0;
            createClick(isAccent);
            
            setCurrentBeat(currentBeatRef.current);
            
            const secondsPerBeat = 60.0 / bpm;
            nextNoteTimeRef.current += secondsPerBeat;
            
            currentBeatRef.current = (currentBeatRef.current + 1) % timeSignature.beats;
        }
    };

    const startMetronome = () => {
        if (!audioContextRef.current) {
            audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        currentBeatRef.current = 0;
        nextNoteTimeRef.current = audioContextRef.current.currentTime;
        
        intervalRef.current = setInterval(scheduler, 25);
        setIsPlaying(true);
    };

    const stopMetronome = () => {
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
        setIsPlaying(false);
        setCurrentBeat(0);
        currentBeatRef.current = 0;
    };

    const handleBpmChange = (newBpm) => {
        const clampedBpm = Math.max(20, Math.min(300, newBpm));
        setBpm(clampedBpm);
    };

    const tapTimes = useRef([]);
    const handleTapTempo = () => {
        const now = Date.now();
        tapTimes.current.push(now);
        
        // Keep only last 4 taps
        if (tapTimes.current.length > 4) {
            tapTimes.current.shift();
        }
        
        if (tapTimes.current.length >= 2) {
            const intervals = [];
            for (let i = 1; i < tapTimes.current.length; i++) {
                intervals.push(tapTimes.current[i] - tapTimes.current[i - 1]);
            }
            const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
            const newBpm = Math.round(60000 / avgInterval);
            handleBpmChange(newBpm);
        }
        
        // Reset if no tap for 2 seconds
        setTimeout(() => {
            if (Date.now() - tapTimes.current[tapTimes.current.length - 1] > 2000) {
                tapTimes.current = [];
            }
        }, 2000);
    };

    useEffect(() => {
        return () => {
            stopMetronome();
            if (audioContextRef.current) {
                audioContextRef.current.close();
            }
        };
    }, []);

    // Update scheduler when BPM changes during playback
    useEffect(() => {
        if (isPlaying) {
            stopMetronome();
            startMetronome();
        }
    }, [bpm, timeSignature]);

    return (
        <div className="metronome-panel">
            <div className="metronome-header">
                <h2 className="metronome-title">Metronome</h2>
                <button 
                    className={`metronome-toggle ${isPlaying ? 'active' : ''}`}
                    onClick={isPlaying ? stopMetronome : startMetronome}
                >
                    {isPlaying ? 'Stop' : 'Start'}
                </button>
            </div>

            <div className="bpm-display">
                <span className="bpm-value">{bpm}</span>
                <span className="bpm-label">BPM</span>
            </div>

            <div className="bpm-controls">
                <button 
                    className="bpm-btn"
                    onClick={() => handleBpmChange(bpm - 5)}
                >
                    -5
                </button>
                <button 
                    className="bpm-btn"
                    onClick={() => handleBpmChange(bpm - 1)}
                >
                    -1
                </button>
                <input
                    type="range"
                    min="20"
                    max="300"
                    value={bpm}
                    onChange={(e) => handleBpmChange(parseInt(e.target.value))}
                    className="bpm-slider"
                />
                <button 
                    className="bpm-btn"
                    onClick={() => handleBpmChange(bpm + 1)}
                >
                    +1
                </button>
                <button 
                    className="bpm-btn"
                    onClick={() => handleBpmChange(bpm + 5)}
                >
                    +5
                </button>
            </div>

            <button className="tap-tempo-btn" onClick={handleTapTempo}>
                Tap Tempo
            </button>

            <div className="beat-indicator">
                {Array.from({ length: timeSignature.beats }).map((_, i) => (
                    <div 
                        key={i}
                        className={`beat-dot ${currentBeat === i && isPlaying ? 'active' : ''} ${i === 0 ? 'accent' : ''}`}
                    />
                ))}
            </div>

            <div className="time-signature-selector">
                <span className="ts-label">Time Signature</span>
                <div className="ts-options">
                    {TIME_SIGNATURES.map((ts) => (
                        <button
                            key={ts.label}
                            className={`ts-btn ${timeSignature.label === ts.label ? 'active' : ''}`}
                            onClick={() => setTimeSignature(ts)}
                        >
                            {ts.label}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
