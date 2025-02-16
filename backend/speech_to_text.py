import os
import tempfile
import time
import traceback
import subprocess

from flask import Blueprint, request, jsonify, send_file
import requests
from pydub import AudioSegment  # for converting audio formats
from extensions import llama_client

# Create the blueprint for speech-related endpoints.
speech_to_text_bp = Blueprint('speech_to_text', __name__, url_prefix='/speech')

# Global variable to hold conversation context.
conversation_context = []

# Configuration for remote playback
RASPBERRY_PI_IP = "192.168.11.2"  # Replace with your Pi's IP address
REMOTE_PLAY_SCRIPT = "/home/pi/AIY-projects-python/checkpoints/play_wav.py"

def _transcribe_audio(file_path: str):
    """
    Transcribe audio by sending it to a local inference endpoint.
    The endpoint is expected to return JSON with a "text" key.
    """
    with open(file_path, 'rb') as audio_file:
        url = "http://127.0.0.1:8080/inference"
        files = {"file": audio_file}
        data = {"temperature": "0.0", "temperature_inc": "0.2"}
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()
        result = response.json()
        return result.get("text", "")

def save_pcm_to_wav(pcm_data, file_path):
    """
    Convert raw PCM data to a WAV file.
    """
    import wave
    with wave.open(file_path, 'wb') as wav_file:
        wav_file.setnchannels(1)     # Mono
        wav_file.setsampwidth(2)       # 16-bit samples
        wav_file.setframerate(16000)   # 16 kHz sampling rate
        wav_file.writeframes(pcm_data)

def transcribe_audio_route(audio_file):
    """
    Save the uploaded audio to a temporary WAV file and transcribe it.
    """
    if not audio_file:
        raise ValueError("No audio file provided")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        audio_file.save(temp_audio.name)
        try:
            transcription = _transcribe_audio(temp_audio.name)
            return transcription
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {str(e)}")
        finally:
            os.remove(temp_audio.name)

def chat_reply(transcription):
    """
    Generate a chat reply using your offline chat engine.
    The conversation_context is updated with the new transcription and reply.
    """
    global conversation_context
    try:
        system_prompt = "You are an education tool."
        # Build the message sequence.
        message = [{"role": "system", "content": system_prompt}]
        message.extend(conversation_context)
        message.append({"role": "user", "content": transcription})
        conversation_context.append({"role": "user", "content": transcription})

        completion = llama_client.chat.completions.create(
            model="gpt-4o-mini",  # Adjust to your actual model name
            messages=conversation_context,
        )
        reply = completion.choices[0].message.content
        conversation_context.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        raise RuntimeError(f"Chat reply failed: {str(e)}")

def generate_speech(text, output_file="output.mp3"):
    """
    Generate speech audio from the given text using the Kokoro model.
    Saves the output to a file and returns the file path.
    """
    try:
        from openai import OpenAI  # Ensure your OpenAI client supports this usage.
        client = OpenAI(
            base_url="http://localhost:8880/v1",  # Adjust as necessary
            api_key="not-needed"  # If your local server does not require an API key
        )
        with client.audio.speech.with_streaming_response.create(
            model="kokoro",
            voice="af_sky+af_bella",  # Adjust as needed
            input=text
        ) as response:
            response.stream_to_file(output_file)
        return output_file
    except Exception as e:
        raise RuntimeError(f"Speech synthesis failed: {str(e)}")

def convert_mp3_to_wav(mp3_file, wav_file="output.wav"):
    """
    Convert an MP3 file to WAV format.
    Returns the WAV file path.