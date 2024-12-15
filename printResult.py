import json
import time
import threading
import paho.mqtt.client as mqtt

# --------------------- Configuration ---------------------
# MQTT Configuration (TCP - Local)
BROKER = "localhost"  # MQTT Broker địa chỉ (TCP)
MQTT_PORT = 1883
MQTT_TOPIC = "emotion_topic"

# WebSocket MQTT Configuration
WS_BROKER = "broker.emqx.io"
WS_PORT = 8083

# Biến quản lý
receive_from_mqtt = False  # Ban đầu chỉ nghe từ WebSocket broker
# Khi nhận "switch_to_mqtt" từ WebSocket broker, chuyển sang nghe MQTT local.

mqtt_client = None
ws_mqtt_client = None

# --------------------- Callbacks --------------------

def on_message_mqtt(client, userdata, msg):
    global receive_from_mqtt
    # Nếu đang ở chế độ nhận từ MQTT local thì xử lý, nếu không thì bỏ qua
    if receive_from_mqtt:
        try:
            decoded_msg = msg.payload.decode().strip()
            print(f"[MQTT LOCAL] Message received on {msg.topic}: {decoded_msg}")
            # Parse JSON
            emotion_data = json.loads(decoded_msg)
            emotion = emotion_data.get("emotion", "")
            print(f"[MQTT LOCAL] Processed Emotion: {emotion}")
        except json.JSONDecodeError as e:
            print(f"[MQTT LOCAL] Error decoding message: {e}")
        except Exception as e:
            print(f"[MQTT LOCAL] Error processing message: {e}")
    else:
        print("[MQTT LOCAL] Ignoring messages (WebSocket mode active).")


def on_message_ws(client, userdata, msg):
    global receive_from_mqtt
    try:
        decoded_msg = msg.payload.decode().strip()
        parsed_message = json.loads(decoded_msg)

        source = parsed_message.get("source", "")
        ai_value = parsed_message.get("ai", None)

        # Kiểm tra có phải lệnh điều khiển không
        if source == "web" and ai_value is not None:
            # Đây là lệnh điều khiển bật/tắt AI mode (1883)
            if str(ai_value).lower() == "true":
                receive_from_mqtt = True
                print("[MQTT WS] Switching to MQTT (1883) mode (ai = true).")
            else:
                receive_from_mqtt = False
                print("[MQTT WS] Switching to WebSocket (8083) mode (ai = false).")
        else:
            # Không phải lệnh điều khiển, là dữ liệu thường
            if not receive_from_mqtt:
                # Chỉ forward sang MQTT local nếu đang ở chế độ WS
                if mqtt_client:
                    mqtt_client.publish(MQTT_TOPIC, json.dumps(parsed_message))
                    print(f"[MQTT WS] Forwarded message to MQTT local: {parsed_message}")
            else:
                # Nếu đang ở chế độ 1883, bỏ qua tin nhắn dữ liệu thường
                # nhưng KHÔNG bỏ qua lệnh điều khiển (đã xử lý ở trên).
                pass

    except json.JSONDecodeError as e:
        print(f"[MQTT WS] Error decoding message: {e}")
    except Exception as e:
        print(f"[MQTT WS] Error processing message: {e}")


# --------------------- Setup Functions --------------------
def setup_mqtt_local():
    client = mqtt.Client()
    client.on_message = on_message_mqtt
    try:
        client.connect(BROKER, MQTT_PORT, keepalive=60)
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to MQTT (TCP) topic: {MQTT_TOPIC}")
        return client
    except Exception as e:
        print(f"Error connecting to MQTT broker (TCP): {e}")
        return None

def setup_mqtt_ws():
    client = mqtt.Client(transport="websockets")
    client.on_message = on_message_ws
    try:
        client.connect(WS_BROKER, WS_PORT, keepalive=60)
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to MQTT (WebSocket) topic: {MQTT_TOPIC}")
        return client
    except Exception as e:
        print(f"Error connecting to MQTT broker (WS): {e}")
        return None

# --------------------- Main Execution --------------------
if __name__ == "__main__":
    # MQTT local client
    mqtt_client = setup_mqtt_local()
    if mqtt_client:
        mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
        mqtt_thread.daemon = True
        mqtt_thread.start()

    # MQTT WebSocket client
    ws_mqtt_client = setup_mqtt_ws()
    if ws_mqtt_client:
        ws_mqtt_thread = threading.Thread(target=ws_mqtt_client.loop_forever)
        ws_mqtt_thread.daemon = True
        ws_mqtt_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program interrupted by user. Exiting...")
    finally:
        if mqtt_client:
            mqtt_client.disconnect()
            print("Disconnected from MQTT (TCP).")
        if ws_mqtt_client:
            ws_mqtt_client.disconnect()
            print("Disconnected from MQTT (WebSocket).")
