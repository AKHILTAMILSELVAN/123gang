import numpy as np
import sounddevice as sd
import time
import pyttsx3
import random
import threading
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# Parameters
fs = 44100  # Sampling rate
duration = 1  # seconds
chirp_freq = 18000  # Hz
objects = ["a wall", "a chair", "a table", "a person", "a book", "a window", "a door"]

# 🔊 Threaded safe TTS to avoid "run loop already started"
def speak(message):
    def _speak():
        try:
            local_engine = pyttsx3.init()
            local_engine.say(message)
            local_engine.runAndWait()
        except Exception as e:
            print("🔇 Error speaking:", e)

    t = threading.Thread(target=_speak)
    t.daemon = True
    t.start()

# 🏠 Home route
@app.route('/')
def index():
    return render_template('index.html')

# 📡 Main echolocation route
@app.route('/echolocation')
def echolocation():
    print("🔁 /echolocation route called")
    try:
        print("🎵 Emitting chirp...")
        emit_chirp()

        print("🎙️ Listening for echo...")
        start_time = time.time()
        recording = listen_for_echo()
        end_time = time.time()

        echo_amplitude = np.max(np.abs(recording))
        print(f"📈 Max amplitude: {echo_amplitude}")
        threshold = 0.01

        if echo_amplitude > threshold:
            echo_time = end_time - start_time
            distance = calculate_distance(echo_time)
            obj = "an object"
            mode = "Real echo"
        else:
            obj, distance = simulate_object()
            mode = "Simulated echo"

        message = f"{mode}: Detected {obj} approximately {distance:.2f} cm away."
        print("✅", message)

        # 🔊 Speak using safe threaded engine
        speak(f"Detected {obj} approximately {distance:.2f} centimeters away.")

        # 📝 Save log
        with open("echolog.txt", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

        return jsonify({
            "object": obj,
            "distance": f"{distance:.2f}",
            "message": message
        })

    except Exception as e:
        print("❌ Error during echolocation:", e)
        return jsonify({
            "object": "error",
            "distance": "0",
            "message": "Echolocation failed due to an error."
        }), 500

# 🔊 Emit high frequency chirp (18kHz)
def emit_chirp():
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    chirp = 0.5 * np.sin(2 * np.pi * chirp_freq * t)
    sd.play(chirp, fs)
    sd.wait()

# 🎤 Listen for echo
def listen_for_echo():
    recording_duration = 0.1  # seconds
    recording = sd.rec(int(recording_duration * fs), samplerate=fs, channels=1, dtype='float64')
    sd.wait()
    return recording

# 📏 Calculate distance from time
def calculate_distance(echo_time):
    speed_of_sound = 34300  # cm/s
    return (echo_time * speed_of_sound) / 2

# 🧠 Simulate object if no echo is found
def simulate_object():
    obj = random.choice(objects)
    dist = random.uniform(50, 300)
    return obj, dist

# 🚀 Start Flask server
if __name__ == '__main__':
    app.run(debug=True)
