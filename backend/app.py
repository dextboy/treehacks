import os
import time
import wave
import audioop
import sqlite3
import threading
import pyaudio
import requests
from flask import Flask, jsonify
from flask_socketio import SocketIO
from socket_routes import register_socket_events
from speech_to_text import speech_to_text_bp
from yolo import process_video_stream
from extensions import llama_client

# Configuration for recording
THRESHOLD = 1000          # RMS threshold for silence
SILENCE_CHUNKS = 30       # Number of consecutive silent chunks
CHUNK = 1024              # Audio samples per frame
FORMAT = pyaudio.paInt16  # 16-bit format
CHANNELS = 1              # Mono audio
RATE = 16000              # Sample rate in Hz
OUTPUT_WAV = "output.wav"
API_URL = "http://localhost:5001/speech/process"

# Database path
database_path = "student_data.db"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Register Socket.IO events and blueprint
register_socket_events(socketio)
app.register_blueprint(speech_to_text_bp)


def fetch_student_scores(name):
    """
    Fetch student scores from the database.
    """
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        query = """SELECT Reading, Writing, Speaking, Vocabulary FROM Student WHERE Name = ?"""
        cursor.execute(query, (name,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "Reading": result[0],
                "Writing": result[1],
                "Speaking": result[2],
                "Vocabulary": result[3]
            }
        else:
            return {"error": "Student not found"}
    except sqlite3.Error as e:
        print("Error while connecting to database:", e)
        return {"error": "Database error"}


def query_llama_for_lowest_component(lowest_component):
    """
    Query the llama model for advice or explanation based on the lowest component.
    """
    try:
        system_prompt = "You are an educational assistant. Provide guidance for improvement."
        user_prompt = f"The student's lowest skill is {lowest_component}. Give practice exercises to improve it."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        completion = llama_client.chat.completions.create(
            model="gpt-4o-mini",  # Adjust to your actual model name
            messages=messages,
        )

        reply = completion.choices[0].message.content
        return reply

    except Exception as e:
        print(f"Error querying llama model: {e}")
        return "Error querying llama model"


def process_new_name(new_name):
    """
    Process the new name by fetching data, determining the lowest score,
    and querying the llama model.
    """
    print(f"Extracted Name: {new_name}")
    student_data = fetch_student_scores(new_name)

    # Check if there's an error in the student data
    if "error" in student_data:
        print(student_data["error"])
        return

    lowest = float("inf")
    lowest_component = None

    # Iterate over the student's scores to find the lowest one
    for component, score in student_data.items():
        try:
            score_val = float(score)
            if score_val < lowest:
                lowest = score_val
                lowest_component = component
        except (ValueError, TypeError):
            continue

    if lowest_component:
        llama_response = query_llama_for_lowest_component(lowest_component)
        print("Advice from llama model:", llama_response)


def record_until_silence():
    """
    Record audio until silence is detected and save it as a WAV file.
    """
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording... speak into the microphone.")
    frames = []
    silence_counter = 0

    try:
        while True:
            data = stream.read(CHUNK)
            frames.append(data)
            rms = audioop.rms(data, 2)  # Calculate Root Mean Square (RMS)
            if rms < THRESHOLD:
                silence_counter += 1
            else:
                silence_counter = 0

            if silence_counter > SILENCE_CHUNKS:
                print("Silence detected. Stopping recording.")
                break
    except Exception as e:
        print("Error during recording:", e)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    # Save the recorded audio to a WAV file
    with wave.open(OUTPUT_WAV, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    print("Recording saved to", OUTPUT_WAV)
    try:
        with open(OUTPUT_WAV, 'rb') as f:
            files = {'audio': f}
            response = requests.post(API_URL, files=files)
            if response.status_code == 200:
                print("API Response:", response.json())
            else:
                print(f"Failed to process speech. Status code: {response.status_code}, Error: {response.text}")
    except Exception as e:
        print("Error sending file to API:", e)
    return OUTPUT_WAV


def monitor_video_stream():
    """
    Background task that continuously monitors the video stream for a new name.
    """
    current_name = None
    while True:
        new_name = process_video_stream()
        record_until_silence()  # Start recording after processing
        if new_name and new_name != current_name:
            current_name = new_name
            process_new_name(new_name)
        time.sleep(10)


@app.route('/student/<name>')
def get_student(name):
    """
    API to fetch student scores by name.
    """
    data = fetch_student_scores(name)
    return jsonify(data)


@app.route('/record', methods=['GET'])
def start_recording():
    """
    API to start recording audio until silence is detected.
    """
    try:
        wav_file = record_until_silence()
        return jsonify({"status": "success", "file_path": wav_file})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Start a background thread for continuous monitoring and recording
    monitor_thread = threading.Thread(target=monitor_video_stream, daemon=True)
    monitor_thread.start()

    # Run the Flask-SocketIO server
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)