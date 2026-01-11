import { useState, useEffect, useRef } from "react";
import "../styles/Tuner.css";

const NOTE_STRINGS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];

// Standard violin tuning frequencies
const VIOLIN_STRINGS = {
    "G3": 196.00,
    "D4": 293.66,
    "A4": 440.00,
    "E5": 659.25
};

// Standard viola tuning frequencies
const VIOLA_STRINGS = {
    "C3": 130.81,
    "G3": 196.00,
    "D4": 293.66,
    "A4": 440.00
};

export default function Tuner() {
    const [isListening, setIsListening] = useState(false);
    const [frequency, setFrequency] = useState(null);
    const [note, setNote] = useState("--");
    const [cents, setCents] = useState(0);
    const [octave, setOctave] = useState(null);
    
    const audioContextRef = useRef(null);
    const analyserRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const rafIdRef = useRef(null);

    const getNote = (freq) => {
        const noteNum = 12 * (Math.log(freq / 440) / Math.log(2));
        return Math.round(noteNum) + 69;
    };

    const getCents = (freq, noteIndex) => {
        const noteFreq = 440 * Math.pow(2, (noteIndex - 69) / 12);
        return Math.floor(1200 * Math.log(freq / noteFreq) / Math.log(2));
    };

    const autoCorrelate = (buffer, sampleRate) => {
        const SIZE = buffer.length;
        const MAX_SAMPLES = Math.floor(SIZE / 2);
        let bestOffset = -1;
        let bestCorrelation = 0;
        let rms = 0;
        let foundGoodCorrelation = false;

        for (let i = 0; i < SIZE; i++) {
            const val = buffer[i];
            rms += val * val;
        }
        rms = Math.sqrt(rms / SIZE);

        if (rms < 0.01) return -1;

        let lastCorrelation = 1;
        for (let offset = 0; offset < MAX_SAMPLES; offset++) {
            let correlation = 0;
            for (let i = 0; i < MAX_SAMPLES; i++) {
                correlation += Math.abs(buffer[i] - buffer[i + offset]);
            }
            correlation = 1 - correlation / MAX_SAMPLES;

            if (correlation > 0.9 && correlation > lastCorrelation) {
                foundGoodCorrelation = true;
                if (correlation > bestCorrelation) {
                    bestCorrelation = correlation;
                    bestOffset = offset;
                }
            } else if (foundGoodCorrelation) {
                const shift = (correlation - lastCorrelation) / (correlation - lastCorrelation);
                return sampleRate / (bestOffset + shift);
            }
            lastCorrelation = correlation;
        }

        if (bestCorrelation > 0.01) {
            return sampleRate / bestOffset;
        }
        return -1;
    };

    const updatePitch = () => {
        if (!analyserRef.current) return;

        const buffer = new Float32Array(analyserRef.current.fftSize);
        analyserRef.current.getFloatTimeDomainData(buffer);

        const freq = autoCorrelate(buffer, audioContextRef.current.sampleRate);

        if (freq > 0 && freq < 2000) {
            setFrequency(freq);
            const noteIndex = getNote(freq);
            const noteName = NOTE_STRINGS[noteIndex % 12];
            const noteOctave = Math.floor(noteIndex / 12) - 1;
            const centsOff = getCents(freq, noteIndex);

            setNote(noteName);
            setOctave(noteOctave);
            setCents(centsOff);
        }

        rafIdRef.current = requestAnimationFrame(updatePitch);
    };

    const startListening = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaStreamRef.current = stream;

            audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
            analyserRef.current = audioContextRef.current.createAnalyser();
            analyserRef.current.fftSize = 2048;

            const source = audioContextRef.current.createMediaStreamSource(stream);
            source.connect(analyserRef.current);

            setIsListening(true);
            updatePitch();
        } catch (err) {
            console.error("Error accessing microphone:", err);
            alert("Unable to access microphone. Please check permissions.");
        }
    };

    const stopListening = () => {
        if (rafIdRef.current) {
            cancelAnimationFrame(rafIdRef.current);
        }
        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach(track => track.stop());
        }
        if (audioContextRef.current) {
            audioContextRef.current.close();
        }
        setIsListening(false);
        setFrequency(null);
        setNote("--");
        setCents(0);
        setOctave(null);
    };

    useEffect(() => {
        return () => {
            stopListening();
        };
    }, []);

    const getTuningStatus = () => {
        if (cents === 0) return "in-tune";
        if (Math.abs(cents) <= 5) return "close";
        if (Math.abs(cents) <= 15) return "slightly-off";
        return "off";
    };

    const tuningStatus = getTuningStatus();

    return (
        <div className="tuner-panel">
            <div className="tuner-header">
                <h2 className="tuner-title">Tuner</h2>
                <button 
                    className={`tuner-toggle ${isListening ? 'active' : ''}`}
                    onClick={isListening ? stopListening : startListening}
                >
                    {isListening ? 'Stop' : 'Start'}
                </button>
            </div>

            <div className="tuner-display">
                <div className={`note-display ${tuningStatus}`}>
                    <span className="note-name">{note}</span>
                    {octave !== null && <span className="note-octave">{octave}</span>}
                </div>
                
                <div className="cents-meter">
                    <div className="cents-scale">
                        <span>-50</span>
                        <span>0</span>
                        <span>+50</span>
                    </div>
                    <div className="cents-bar">
                        <div className="cents-center"></div>
                        <div 
                            className={`cents-indicator ${tuningStatus}`}
                            style={{ 
                                left: `${50 + Math.max(-50, Math.min(50, cents))}%`
                            }}
                        ></div>
                    </div>
                </div>

                {frequency && (
                    <div className="frequency-display">
                        <span className="frequency-value">{frequency.toFixed(1)}</span>
                        <span className="frequency-unit">Hz</span>
                    </div>
                )}
            </div>

            <div className="violin-strings">
                <span className="strings-label">Violin Strings</span>
                <div className="strings-grid">
                    {Object.entries(VIOLIN_STRINGS).map(([name, freq]) => (
                        <div key={name} className="string-reference">
                            <span className="string-name">{name}</span>
                            <span className="string-freq">{freq} Hz</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className="viola-strings">
                <span className="strings-label">Viola Strings</span>
                <div className="strings-grid">
                    {Object.entries(VIOLA_STRINGS).map(([name, freq]) => (
                        <div key={name} className="string-reference">
                            <span className="string-name">{name}</span>
                            <span className="string-freq">{freq} Hz</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
