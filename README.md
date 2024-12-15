# Emotion Detection Project

This project implements a real-time emotion detection system using AI models and MQTT communication. It includes:

- **`emotion_demo.py`**: Core AI script for emotion detection.
- **`printResult.py`**: Script to display results and handle control commands via MQTT.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Usage](#usage)
   - [Start Mosquitto Broker](#1-start-mosquitto-broker)
   - [Run the Emotion Detection Script](#2-run-the-emotion-detection-script)
   - [Run the Result Display Script](#3-run-the-result-display-script)
3. [File Details](#file-details)
4. [Troubleshooting](#troubleshooting)
5. [License](#license)

---

## Prerequisites

1. **Python Installation**
   Ensure Python (>=3.7) is installed. [Download Python](https://www.python.org/).

2. **Mosquitto Installation**
   Install Mosquitto MQTT broker version **2.0.12**.  
   > **Note:** The latest versions may not support WebSocket communication. Version 2.0.12 is confirmed to work.

   - **Windows**: [Download Mosquitto 2.0.12](https://mosquitto.org/download/).
   - **Linux**:
     ```bash
     sudo apt update
     sudo apt install -y mosquitto=2.0.12 mosquitto-clients
     ```
   - **MacOS**:
     ```bash
     brew install mosquitto@2.0.12
     ```

   To verify the installed version:
   ```bash
   mosquitto -v
   ```

3. **Dependencies Installation**
   Install the required Python libraries:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Start Mosquitto Broker
Run the Mosquitto MQTT broker with WebSocket support enabled (default port **8083**):
```bash
mosquitto
```

### 2. Run the Emotion Detection Script
Execute the `emotion_demo.py` script to start the emotion detection:
```bash
python emotion_demo.py
```

### 3. Run the Result Display Script
Run `printResult.py` to subscribe to the MQTT topic and display results:
```bash
python printResult.py
```

---

## File Details

- **`emotion_demo.py`**: 
  - Loads a pre-trained model (`emotion_detection.h5`) and uses a Haar Cascade classifier (`haarcascade_frontalface_default.xml`) for face detection.
  - Publishes results via MQTT.
  - Update the absolute path to the model if necessary:
    ```python
    classifier = load_model('C:/Users/manhh/Downloads/emotion detect/emotion_detection.h5')
    ```

- **`printResult.py`**: 
  - Subscribes to two MQTT brokers:
    - Local MQTT broker (TCP, port **1883**).
    - WebSocket MQTT broker (port **8083**).
  - Dynamically switches between local MQTT and WebSocket brokers based on control commands.
    - **Control Commands:** Received via WebSocket, with key `ai` to toggle AI mode:
      - `ai: true`: Switches to local MQTT (1883) for emotion messages.
      - `ai: false`: Switches back to WebSocket (8083).
  - Forwards messages from WebSocket broker to local MQTT when in WebSocket mode.
  - Example processing flow:
    1. Receives JSON messages containing `emotion` data or control commands.
    2. Decodes and processes messages based on their source.
    3. Prints processed emotions or logs forwarded messages.

- **`emotion_detection.h5`**: Pre-trained model for emotion classification.

- **`haarcascade_frontalface_default.xml`**: Haar Cascade XML for face detection.

- **`requirements.txt`**: Python dependencies for the project.

---

## Troubleshooting

1. **Mosquitto not running:**
   Ensure Mosquitto version 2.0.12 is installed and running:
   ```bash
   mosquitto
   ```

2. **WebSocket issues:**
   Verify that Mosquitto is configured to listen on port **8083**. Check the configuration file (usually located at `/etc/mosquitto/mosquitto.conf`) and ensure it includes:
   ```plaintext
   listener 8083
   protocol websockets
   ```

3. **Missing dependencies:**
   Reinstall the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. **FileNotFoundError:**
   Verify all required files (`emotion_detection.h5`, `haarcascade_frontalface_default.xml`) are in the correct directory.

---

## Example Output

**From `printResult.py`:**
```
[MQTT LOCAL] Message received on emotion_topic: {"emotion": "Happy"}
[MQTT LOCAL] Processed Emotion: Happy
[MQTT WS] Forwarded message to MQTT local: {"emotion": "Neutral"}
[MQTT WS] Switching to MQTT (1883) mode (ai = true).
```

---

## License

Feel free to use and modify this file as needed.

