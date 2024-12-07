import paho.mqtt.client as mqtt
import json
import serial  # Đảm bảo là pyserial được import đúng
import time

# --------------------- Configuration ---------------------
# MQTT Configuration
BROKER = "localhost"  # Change to your broker's IP if needed
PORT = 1883
TOPIC = "emotion_topic"

# Serial Configuration
SERIAL_PORT = "COM7"  # Replace with your serial port (e.g., COM3 on Windows or /dev/ttyUSB0 on Linux)
BAUD_RATE = 9600      # Ensure this matches the baud rate of your serial device
# ----------------------------------------------------------

# Initialize Serial Connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)  # Wait for the serial connection to initialize
    print(f"Connected to serial port {SERIAL_PORT} at {BAUD_RATE} baud.")
except serial.SerialException as e:
    print(f"Error connecting to serial port: {e}")
    ser = None  # Set to None to handle absence of serial connection gracefully

# Variable to store current light settings
current_light_settings = {
    "brightness": 100,   # Default brightness
    "color": "white",    # Default color
    "status": "on"       # Default status
}

# Function to send data via serial
def send_via_serial(data):
    if ser and ser.is_open:
        try:
            json_data = json.dumps(data)
            ser.write((json_data + "\n").encode())  # Send as JSON string with newline
            print(f"Sent via serial: {json_data}")
        except serial.SerialException as e:
            print(f"Error sending data via serial: {e}")
    else:
        print("Serial port is not open. Cannot send data.")

# Callback function when a message is received
def on_message(client, userdata, msg):
    try:
        # Print the raw received message
        print(f"Raw message received: {msg.payload}")

        # Decode the JSON message
        decoded_msg = msg.payload.decode().strip()
        print(f"Decoded message: {decoded_msg}")

        # Check if the message is empty or invalid
        if decoded_msg == "{}" or not decoded_msg:
            print("Received empty or invalid emotion, skipping.")
            return

        # Parse JSON
        try:
            emotion_data = json.loads(decoded_msg)
            emotion = emotion_data.get("emotion", "").strip()  # Remove any whitespace
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return

        # Validate emotion
        if not emotion:
            print("Emotion is empty or invalid, skipping.")
            return

        print(f"Decoded emotion: {emotion}")

        # Determine new light settings based on emotion
        new_light_settings = {}

        if emotion == "Happy":
            new_light_settings = {
                "brightness": 255,   # Maximum brightness
                "color": "green",   # Bright yellow color
                "status": "on"
            }
        elif emotion == "Sad":
            new_light_settings = {
                "brightness": 50,    # Low brightness
                "color": "yellow",     # Blue color
                "status": "on"
            }
        elif emotion == "Angry":
            new_light_settings = {
                "brightness": 255,   # Maximum brightness
                "color": "red",      # Red color
                "status": "on"    # Blink status
            }
        elif emotion == "Surprise":
            new_light_settings = {
                "brightness": 255,   # Maximum brightness
                "color": "red",   # Purple color
                "status": "on"
            }
        elif emotion == "Neutral":
            new_light_settings = {
                "brightness": 100,   # Medium brightness
                "color": "blue",    # White color
                "status": "on"
            }
        else:
            print(f"Unrecognized emotion: {emotion}, skipping.")
            return

        # Check if there is a change in light settings
        if new_light_settings != current_light_settings:
            # Update current settings
            current_light_settings.update(new_light_settings)

            # Send the new settings via serial
            send_via_serial(new_light_settings)
        else:
            print("No change in light settings, nothing to send.")

    except Exception as e:
        print(f"Error processing message: {e}")

# Initialize MQTT Client
client = mqtt.Client()
client.on_message = on_message

# Connect to MQTT Broker and Subscribe to Topic
try:
    client.connect(BROKER, PORT, 60)
    client.subscribe(TOPIC)
    print("Subscribed to MQTT topic and listening for emotions...")
except Exception as e:
    print(f"Error connecting to MQTT broker: {e}")
    if ser and ser.is_open:
        ser.close()
    exit(1)

# Start MQTT Loop in a Separate Thread
client.loop_start()

print("Listening for emotions... Press Ctrl+C to exit.")

# Keep the main thread alive to allow continuous listening
try:
    while True:
        time.sleep(1)  # Sleep to reduce CPU usage
except KeyboardInterrupt:
    print("\nProgram interrupted by user. Exiting...")
finally:
    # Clean up resources
    if ser and ser.is_open:
        ser.close()
        print(f"Closed serial port {SERIAL_PORT}.")
    client.loop_stop()
    client.disconnect()
    print("Disconnected from MQTT broker.")
