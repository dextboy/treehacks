import pyaudio
import wave
import audioop
import time

# Configuration parameters
THRESHOLD = 1000          # RMS threshold for silence (lower = more sensitive)
SILENCE_CHUNKS = 30       # Number of consecutive silent chunks required to stop recording
CHUNK = 1024              # Number of audio samples per frame
FORMAT = pyaudio.paInt16  # 16-bit resolution
CHANNELS = 1              # Mono audio
RATE = 16000              # 16 kHz sample rate
OUTPUT_WAV = "output.wav"

def record_until_silence():
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
            # Calculate Root Mean Square (RMS) value from the audio chunk
            rms = audioop.rms(data, 2)  # width=2 for 16-bit audio
            # If the volume is below threshold, count it as silence
            if rms < THRESHOLD:
                silence_counter += 1
            else:
                silence_counter = 0

            # If we have enough consecutive silent chunks, stop recording
            if silence_counter > SILENCE_CHUNKS:
                print("Silence detected. Stopping recording.")
                break
    except KeyboardInterrupt:
        print("Recording interrupted by user.")
    except Exception as e:
        print("Error while recording:", e)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    # Save the recorded frames as a WAV file
    with wave.open(OUTPUT_WAV, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        
    print("Saved recording to", OUTPUT_WAV)
    return OUTPUT_WAV

if __name__ == '__main__':
    record_until_silence()