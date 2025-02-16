import time
import sqlite3
from flask import Flask, jsonify
from flask_socketio import SocketIO
from socket_routes import register_socket_events
from speech_to_text import speech_to_text_bp
from yolo import process_video_stream
from extensions import llama_client

database_path = "student_data.db"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Register Socket.IO events and blueprint
register_socket_events(socketio)
app.register_blueprint(speech_to_text_bp)

def fetch_student_scores(name):
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
    """Process the new name by fetching data, determining the lowest score, and querying the llama model."""
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
        # Ensure score is a number before comparing
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
        # Optionally, emit the new advice to connected clients:
        socketio.emit('student_update', {
            'name': new_name,
            'student_data': student_data,
            'lowest_component': lowest_component,
            'advice': llama_response
        })
    else:
        print("Could not determine the lowest component.")

def monitor_video_stream():
    """Background task that continuously monitors the video stream for a new name."""
    current_name = None
    while True:
        new_name = process_video_stream()  # This function should return a name when detected.
        if new_name and new_name != current_name:
            current_name = new_name
            process_new_name(new_name)
        # Sleep a short while to avoid a busy loop.
        time.sleep(0.5)

@app.route('/student/<name>')
def get_student(name):
    data = fetch_student_scores(name)
    return jsonify(data)

if __name__ == '__main__':
    # Start the background task using Socket.IO's helper
    socketio.start_background_task(target=monitor_video_stream)
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
