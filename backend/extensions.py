from flask_socketio import SocketIO
from openai import OpenAI
from dotenv import load_dotenv
from elevenlabs import ElevenLabs
import os

load_dotenv()

socketio = SocketIO()
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
llama_client = OpenAI(
    base_url="http://localhost:8081/v1", # "http://<Your api-server IP>:port"
    api_key = "sk-no-key-required"
)
eleven_labs_client = ElevenLabs(api_key=os.getenv('ELEVEN_API_KEY'))