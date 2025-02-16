from flask import Flask, jsonify
from flask_socketio import SocketIO
from socket_routes import register_socket_events
from speech_to_text import speech_to_text_bp
from yolo import process_video_stream
import sqlite3
from extensions import llama_client


database_path = "student_data.db"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Register Socket.IO events
register_socket_events(socketio)

# Register the speech-to-text blueprint with URL prefix /speech
app.register_blueprint(speech_to_text_bp)

# Get the name from video processing
name_val = process_video_stream()
print(f"Extracted Name: {name_val}")

# Fetch student scores from the database
def fetch_student_scores(name):
    try:
        # Establishing the connection
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # SQL Query to fetch Reading, Writing, Speaking, Vocabulary for the given name
        query = """SELECT Reading, Writing, Speaking, Vocabulary FROM Student WHERE Name = ?"""
        cursor.execute(query, (name,))
        result = cursor.fetchone()

        # Close the connection
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

# Fetch data for the detected name
student_data = fetch_student_scores(name_val)
lowest = 100
lowest_component = None
for each in student_data:
    if (student_data[each] < lowest) :
        lowest = student_data[each]
        lowest_component = each

        

lowest_llama_response = query_llama_for_lowest_component(lowest_component)
print("Advice from llama model:", lowest_llama_response)

def get_student(name):
    data = fetch_student_scores(name)
    return jsonify(data)


def query_llama_for_lowest_component(lowest_component):
    """
    Query the llama model for advice or explanation based on the lowest component.
    """
    try:
        # Create a prompt or conversation messages for the llama model
        system_prompt = "You are an educational assistant. Provide guidance for improvement."
        user_prompt = f"The student's lowest skill is {lowest_component}. Give practice to improve it."

        # Format your conversation context/messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Make the call to the llama model
        completion = llama_client.chat.completions.create(
            model="gpt-4o-mini",   # Adjust to your actual model name
            messages=messages,
        )

        # Extract the model's response
        reply = completion.choices[0].message.content
        return reply

    except Exception as e:
        print(f"Error querying llama model: {e}")
        return "Error querying llama model"


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
