from flask import Flask
from flask_socketio import SocketIO
from socket_routes import register_socket_events
from speech_to_text import speech_to_text_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Initialize Socket.IO
socketio = SocketIO(app, cors_allowed_origins="*")

# Register Socket.IO events
register_socket_events(socketio)

# Register the speech-to-text blueprint with URL prefix /speech
app.register_blueprint(speech_to_text_bp)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
