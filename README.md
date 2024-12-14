
# Emotion Detection Project

This project implements a real-time emotion detection system using AI models and MQTT communication. The setup includes:

- **`emotion_demo.py`**: Main AI script for emotion detection.
- **`printResult.py`**: Script to receive and display results through MQTT.

---

## Prerequisites

1. **Python Installation**
   Ensure Python (>=3.7) is installed on your system. You can download Python from [python.org](https://www.python.org/).

2. **Mosquitto Installation**
   Install Mosquitto MQTT broker:
   - **Windows**: Download and install from [Eclipse Mosquitto](https://mosquitto.org/download/).
   - **Linux** (Ubuntu/Debian):
     ```bash
     sudo apt update
     sudo apt install -y mosquitto mosquitto-clients
     ```
   - **MacOS**:
     ```bash
     brew install mosquitto
     ```

3. **Dependencies Installation**
   Install the required Python libraries using the `requirements.txt` file:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Start Mosquitto Broker
Ensure the Mosquitto MQTT broker is running:

```bash
mosquitto
```

### 2. Run the Emotion Detection Script
The `emotion_demo.py` script is the core AI model for emotion detection. Run it as follows:

```bash
python emotion_demo.py
```

### 3. Run the Result Display Script
The `printResult.py` script subscribes to the MQTT topic and displays the emotion detection results:

```bash
python printResult.py
```

---

## File Details

- **`emotion_demo.py`**: Implements the AI model to detect emotions using a pre-trained model (`emotion_detection.h5`) and Haar Cascade classifier (`haarcascade_frontalface_default.xml`). Publishes results via MQTT.

- **`printResult.py`**: Subscribes to the MQTT topic and prints the detected emotions.

- **`emotion_detection.h5`**: Pre-trained model for emotion classification.

- **`haarcascade_frontalface_default.xml`**: Haar Cascade XML for face detection.

- **`requirements.txt`**: Contains a list of Python dependencies for the project.

---

## Troubleshooting

1. **Mosquitto not running:**
   Ensure the Mosquitto broker is installed and running. Use the command:
   ```bash
   mosquitto
   ```

2. **Missing dependencies:**
   Reinstall the dependencies with:
   ```bash
   pip install -r requirements.txt
   ```

3. **FileNotFoundError:**
   Make sure all required files (`emotion_detection.h5`, `haarcascade_frontalface_default.xml`) are in the same directory as the scripts.

---

## License

This project is licensed under the MIT License. Feel free to use and modify it as needed.
