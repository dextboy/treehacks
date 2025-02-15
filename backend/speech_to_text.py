import os
import wave
import tempfile
import requests
from flask import Blueprint, request, jsonify
from extensions import llama_client

# Create the blueprint for speech-related endpoints.
speech_to_text_bp = Blueprint('speech_to_text', __name__, url_prefix='/speech')

# Global variable to hold conversation context.
conversation_context = []

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
        # For demonstration, we define a system prompt.
        system_prompt = "You are an education tool aime"
        # Build the message sequence.
        message = [{"role": "system", "content": system_prompt}]
        message.extend(conversation_context)
        message.append({"role": "user", "content": transcription})
        conversation_context.append({"role": "user", "content": transcription})
        
        # Call your offline chat engine (this should be replaced with your actual API).
        completion = llama_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_context,
        )
        reply = completion.choices[0].message.content
        conversation_context.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        raise RuntimeError(f"Chat reply failed: {str(e)}")

@speech_to_text_bp.route('/process', methods=['POST'])
def process_speech():
    """
    Endpoint that accepts an audio file, transcribes it, and returns a chat reply.
    Expects the audio file to be sent with the key 'audio' in a multipart/form-data POST.
    """
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    audio_file = request.files['audio']
    
    try:
        transcription = transcribe_audio_route(audio_file)
        reply = chat_reply(transcription)
        return jsonify({
            "transcription": transcription,
            "reply": reply
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
