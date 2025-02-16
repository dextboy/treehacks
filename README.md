# Teacher.ai

This project provides functionality to record audio until silence is detected, process the audio using a speech-to-text API, and generate a response with synthesized speech. The application is designed to run on a Jetson device with ALSA and Flask setup.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you start, ensure the following dependencies are installed on your system:

1. **Operating System**: Linux-based system (e.g., Ubuntu) on Jetson devices.
2. **Python**: Python 3.8 or higher installed.
3. **Packages**:
   - `Flask`
   - `Flask-SocketIO`
   - `pyaudio`
   - `requests`
   - `pydub`
4. **ALSA Utilities**:
   - `alsa-utils`
   - `arecord`

Install ALSA utilities using:

```bash
sudo apt update
sudo apt install alsa-utils
```
````

5. **Microphone and Speaker**:
   Ensure your microphone and speaker are properly connected and recognized by the system.

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

2. Set up a Python virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install Python dependencies:

```bash
pip install -r requirements.txt
```

4. Install additional required libraries:

   - `pyaudio` may require the `portaudio` library. Install it using:

   ```bash
   sudo apt install libportaudio2 libportaudiocpp0 portaudio19-dev
   ```

5. Configure ALSA to use the correct audio device:

   - Edit the `~/.asoundrc` file:

     ```bash
     pcm.!default {
         type hw
         card 2
         device 0
     }

     ctl.!default {
         type hw
         card 2
     }
     ```

     Replace `card` and `device` with the appropriate values for your system. Use `arecord -l` to identify them.

---

## Configuration

1. **Set Up Flask Application**:

   - Run the application by navigating to the project directory and starting the Flask server:
     ```bash
     python app.py
     ```

2. **ALSA Setup**:
   - Restart ALSA or reload its configuration:
     ```bash
     sudo alsactl init
     ```

---

## Usage

1. **Start Recording Until Silence**:
   Run the application, and it will start recording audio until silence is detected. The recorded file will be saved as `output.wav`.

2. **Process Recorded Audio**:
   The `output.wav` file will automatically be sent to the `/process/speech` API endpoint for transcription and speech synthesis.

3. **Play Synthesized Speech**:
   The synthesized audio file will be played on the device.

---

## Troubleshooting

1. **ALSA Errors**:

   - If you encounter errors like `Unknown PCM` or `Cannot open device`, verify your `.asoundrc` configuration and check connected audio devices using:
     ```bash
     aplay -l
     arecord -l
     ```

2. **PyAudio Installation**:

   - If `pyaudio` fails to install, ensure the `portaudio` library is installed:
     ```bash
     sudo apt install libportaudio2 libportaudiocpp0 portaudio19-dev
     ```

3. **Permissions Issues**:

   - Ensure you have the required permissions to access audio devices:
     ```bash
     sudo usermod -aG audio $USER
     ```

4. **Device Not Recognized**:
   - Check the microphone and speaker connection. Restart ALSA with:
     ```bash
     sudo alsactl init
     ```

---

## Contributors

- **Your Name** (Project Maintainer)
- [Additional Contributors]

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

```

