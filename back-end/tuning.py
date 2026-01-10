"""
Flask server for violin note detection.
Analyzes audio files and returns the detected musical note.
Uses Parselmouth (Praat) for fast, accurate pitch detection (<100ms response time).
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import parselmouth
from parselmouth.praat import call
import numpy as np
from io import BytesIO
import soundfile as sf
import tempfile
import os

app = Flask(__name__)
CORS(app)

# Note to frequency mapping
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
A4_FREQ = 440.0  # Standard tuning frequency


def frequency_to_note(freq):
    """
    Convert frequency to the nearest note.
    
    Args:
        freq: Frequency in Hz
    
    Returns:
        Dictionary with note name, octave, and exact frequency
    """
    if freq <= 0:
        return None
    
    # Calculate semitones from A4 (440 Hz)
    semitones_from_a4 = 12 * np.log2(freq / A4_FREQ)
    
    # Find nearest semitone
    nearest_semitone = round(semitones_from_a4)
    
    # Calculate note
    note_index = (9 + nearest_semitone) % 12  # A is index 9
    octave = 4 + (9 + nearest_semitone) // 12
    
    note_name = NOTES[note_index]
    
    # Calculate exact frequency of the nearest note
    exact_freq = A4_FREQ * (2 ** (nearest_semitone / 12))
    
    # Calculate cents off (how many cents sharp/flat)
    cents_off = 100 * (np.log2(freq / exact_freq))
    
    return {
        'note': note_name,
        'octave': octave,
        'full_note': f'{note_name}{octave}',
        'frequency': freq,
        'nearest_frequency': exact_freq,
        'cents_off': cents_off,
        'is_sharp': cents_off > 0,
        'is_flat': cents_off < 0
    }


def detect_pitch_praat(audio, sr):
    """
    Detect pitch using Praat's autocorrelation method - VERY FAST and ACCURATE.
    Optimized for monophonic sources like violin.
    
    Args:
        audio: Audio time series (numpy array)
        sr: Sample rate
    
    Returns:
        Tuple of (detected_frequency, confidence)
    """
    # Limit to first 1.5 seconds for speed
    max_samples = min(int(sr * 1.5), len(audio))
    audio = audio[:max_samples]
    
    # Create Praat Sound object directly from numpy array
    sound = parselmouth.Sound(audio, sampling_frequency=sr)
    
    # Extract pitch using autocorrelation (fast and accurate for violin)
    # Violin range: G3 (196 Hz) to A7 (3520 Hz)
    pitch = sound.to_pitch_ac(
        time_step=0.01,  # 10ms steps for speed
        pitch_floor=150,  # Below violin G3
        pitch_ceiling=4000,  # Above violin highest notes
        very_accurate=False  # Faster, still accurate enough
    )
    
    # Get all pitch values
    pitch_values = pitch.selected_array['frequency']
    
    # Filter out unvoiced (0 Hz) segments
    voiced_pitches = pitch_values[pitch_values > 0]
    
    if len(voiced_pitches) == 0:
        return None, 0.0
    
    # Use median for robustness against outliers
    detected_freq = float(np.median(voiced_pitches))
    
    # Calculate confidence based on consistency of pitch values
    if len(voiced_pitches) > 1:
        std_dev = np.std(voiced_pitches)
        # Lower std dev = higher confidence (more consistent pitch)
        confidence = max(0.5, min(1.0, 1.0 - (std_dev / detected_freq)))
    else:
        confidence = 0.7
    
    return detected_freq, float(confidence)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'Violin tuner service is running'})


@app.route('/detect-note', methods=['POST'])
def detect_note():
    """
    Detect the musical note from a violin audio file - ULTRA FAST (<100ms).
    Uses aubio YIN algorithm for accurate pitch detection.
    
    Accepts:
        - Audio file (wav, mp3, ogg, flac, etc.)
    
    Returns:
        JSON with:
        - note: Note name (e.g., 'A4')
        - frequency: Detected frequency in Hz
        - nearest_frequency: Frequency of the nearest note
        - cents_off: How many cents sharp/flat (±50 cents = semitone)
        - confidence: Detection confidence (0-1)
        - is_sharp/is_flat: Whether note is sharp or flat
    """
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Load audio file using soundfile (faster than librosa)
        audio_data = file.read()
        audio, sr = sf.read(BytesIO(audio_data), dtype='float32')
        
        # Convert stereo to mono if needed
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        if len(audio) == 0:
            return jsonify({'error': 'Failed to load audio file'}), 400
        
        # Use Praat for fast, accurate pitch detection
        detected_freq, confidence = detect_pitch_praat(audio, sr)
        
        if detected_freq is None or detected_freq <= 0 or np.isnan(detected_freq):
            return jsonify({
                'success': False,
                'error': 'Could not detect pitch in audio file',
                'note': None,
                'frequency': None,
                'confidence': 0.0
            }), 200
        
        # Convert frequency to note
        note_info = frequency_to_note(detected_freq)
        
        if note_info is None:
            return jsonify({
                'success': False,
                'error': 'Frequency out of musical range',
                'note': None,
                'frequency': detected_freq,
                'confidence': confidence
            }), 200
        
        note_info['confidence'] = float(confidence)
        note_info['frequency'] = float(detected_freq)
        note_info['nearest_frequency'] = float(note_info['nearest_frequency'])
        note_info['cents_off'] = float(note_info['cents_off'])
        note_info['is_sharp'] = bool(note_info['is_sharp'])
        note_info['is_flat'] = bool(note_info['is_flat'])
        
        return jsonify({
            'success': True,
            'note': note_info
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/detect-note-detailed', methods=['POST'])
def detect_note_detailed():
    """
    Detect notes over time in the audio file using aubio.
    Returns a list of detected notes at different time points.
    Fast response time (<500ms for most files).
    """
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Load audio file using soundfile (faster than librosa)
        audio_data = file.read()
        audio, sr = sf.read(BytesIO(audio_data), dtype='float32')
        
        # Convert stereo to mono if needed
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        if len(audio) == 0:
            return jsonify({'error': 'Failed to load audio file'}), 400
        
        # Limit to first 5 seconds for speed
        max_samples = min(int(sr * 5), len(audio))
        audio = audio[:max_samples]
        
        # Create Praat Sound object and extract pitch
        sound = parselmouth.Sound(audio, sampling_frequency=sr)
        pitch = sound.to_pitch_ac(
            time_step=0.02,  # 20ms steps for speed
            pitch_floor=150,
            pitch_ceiling=4000,
            very_accurate=False
        )
        
        notes_list = []
        
        # Get pitch values at each time frame
        times = pitch.xs()
        for t in times:
            freq = pitch.get_value_at_time(t)
            if freq and freq > 0:
                note_info = frequency_to_note(float(freq))
                if note_info:
                    note_info['time'] = float(t)
                    note_info['confidence'] = 0.85
                    note_info['frequency'] = float(freq)
                    note_info['nearest_frequency'] = float(note_info['nearest_frequency'])
                    note_info['cents_off'] = float(note_info['cents_off'])
                    note_info['is_sharp'] = bool(note_info['is_sharp'])
                    note_info['is_flat'] = bool(note_info['is_flat'])
                    notes_list.append(note_info)
        
        if not notes_list:
            return jsonify({
                'success': False,
                'error': 'Could not detect any notes in audio file',
                'notes': []
            }), 200
        
        duration = len(audio) / sr
        
        return jsonify({
            'success': True,
            'notes': notes_list,
            'total_notes': len(notes_list),
            'duration': float(duration)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"Starting Violin Tuner Flask App on port {port}")
    print("Endpoints:")
    print("  GET  /health - Health check")
    print("  POST /detect-note - Detect the main note in audio")
    print("  POST /detect-note-detailed - Detect all notes over time")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
