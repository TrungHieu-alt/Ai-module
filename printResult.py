import json
import time
import threading
import serial  # Thêm thư viện pyserial
import paho.mqtt.client as mqtt
import queue

# --------------------- Configuration ---------------------
# MQTT Configuration (TCP - Local)
BROKER = "localhost"  # MQTT Broker địa chỉ (TCP)
MQTT_PORT = 1883
MQTT_TOPIC = "emotion_topic"

# WebSocket MQTT Configuration
WS_BROKER = "broker.emqx.io"
WS_PORT = 8083
WEBSOCKET_UPDATE_TOPIC = "emotion_updates"  # Chủ đề để gửi cập nhật tới web

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
            
            # Đưa dữ liệu vào hàng đợi để xử lý serial
            userdata['queue'].put(emotion_data)
            
            # Ánh xạ cảm xúc thành màu sắc và cường độ sáng
            mapped_data = map_emotion_to_color_brightness(emotion)
            print(f"[Mapping] Emotion '{emotion}' mapped to {mapped_data}")
            
            # Gửi dữ liệu màu sắc và cường độ sáng qua WebSocket để cập nhật giao diện web
            if ws_mqtt_client:
                ws_mqtt_client.publish(WEBSOCKET_UPDATE_TOPIC, json.dumps(mapped_data))
                print(f"[WebSocket] Sent update to web: {mapped_data}")
                
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
def setup_mqtt_local(queue):
    client = mqtt.Client(userdata={'queue': queue})
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

# --------------------- New Functions for Serial Communication --------------------

def map_emotion_to_color_brightness(emotion):
    """
    Ánh xạ cảm xúc về màu sắc và cường độ sáng.
    """
    emotion_mapping = {
        'Angry': {'color': '#FF0000', 'brightness': 100},
        'Disgusted': {'color': '#00FF00', 'brightness': 80},
        'Fear': {'color': '#0000FF', 'brightness': 70},
        'Happy': {'color': '#FFFF00', 'brightness': 90},
        'Sad': {'color': '#000080', 'brightness': 60},
        'Surprised': {'color': '#FF69B4', 'brightness': 85},
        'Neutral': {'color': '#FFFFFF', 'brightness': 50}
    }
    return emotion_mapping.get(emotion, {'color': '#FFFFFF', 'brightness': 50})



def send_color(color, ser):
    """
    Gửi dữ liệu màu sắc qua cổng serial.
    Định dạng: COLOR:r,g,b\n
    """
    color_str = f"COLOR:{color}\n"
    ser.write(color_str.encode())
    print(f"[Serial] Sent color: {color_str.strip()}")


def send_brightness(brightness, ser):
    """
    Gửi dữ liệu cường độ sáng qua cổng serial.
    Định dạng: BRIGHTNESS:value\n
    """
    brightness_str = f"BRIGHTNESS:{brightness}\n"
    ser.write(brightness_str.encode())
    print(f"[Serial] Sent brightness: {brightness_str.strip()}")


def process_decoded_data_serial(decoded_data, ser):
    """
    Xử lý dữ liệu đã decode và gửi qua serial.
    """
    if not decoded_data:
        print("[Serial] Invalid data received.")
        return

    data_type = decoded_data.get("type")
    value = decoded_data.get("value")

    if data_type == "color":
        send_color(value, ser)
    elif data_type == "brightness":
        send_brightness(value, ser)
    elif data_type == "emotion":
        mapped = map_emotion_to_color_brightness(value)
        send_color(mapped['color'], ser)
        send_brightness(mapped['brightness'], ser)
    else:
        print(f"[Serial] Unsupported data type: {data_type}")


def serial_sender(ser, q):
    """
    Luồng xử lý gửi dữ liệu qua serial từ hàng đợi.
    """
    while True:
        try:
            decoded_data = q.get()
            if decoded_data is None:
                break  # Kết thúc luồng
            process_decoded_data_serial(decoded_data, ser)
        except Exception as e:
            print(f"[Serial Sender] Error: {e}")

# --------------------- Main Execution --------------------
if __name__ == "__main__":
    # Khởi tạo cổng serial COM7 với baudrate 9600 (có thể thay đổi theo yêu cầu)
    try:
        ser = serial.Serial('COM7', 9600, timeout=1)
        time.sleep(2)  # Chờ cổng serial khởi động
        print("Connected to serial port COM7.")
    except serial.SerialException as e:
        print(f"Error opening serial port COM7: {e}")
        ser = None

    # Tạo hàng đợi để truyền dữ liệu từ MQTT sang Serial
    q = queue.Queue()

    # MQTT local client
    mqtt_client = setup_mqtt_local(q)
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

    # Khởi động luồng gửi serial nếu cổng serial đã kết nối
    if ser:
        serial_thread = threading.Thread(target=serial_sender, args=(ser, q))
        serial_thread.daemon = True
        serial_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program interrupted by user. Exiting...")
    finally:
        # Đóng các kết nối MQTT
        if mqtt_client:
            mqtt_client.disconnect()
            print("Disconnected from MQTT (TCP).")
        if ws_mqtt_client:
            ws_mqtt_client.disconnect()
            print("Disconnected from MQTT (WebSocket).")
        # Đóng cổng serial
        if ser:
            q.put(None)  # Đặt None để kết thúc luồng serial
            ser.close()
            print("Closed serial port COM7.")
