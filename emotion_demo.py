import cv2
import numpy as np
from collections import deque
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from PIL import ImageFont, ImageDraw, Image
import paho.mqtt.client as mqtt
import json
import time

# MQTT Configuration
BROKER = "localhost"  # Đổi thành địa chỉ IP của broker nếu cần
PORT = 1883
TOPIC = "emotion_topic"

# Kết nối MQTT
client = mqtt.Client()
client.connect(BROKER, PORT, 60)

# Load mô hình và font chữ
face_classifier = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
classifier = load_model('C:/Users/manhh/Downloads/emotion detect/emotion_detection.h5')
class_labels = ['Angry', 'Disgusted', 'Fear', 'Happy', 'Sad', 'Surprised', 'Neutral']
font_path = "./arial.ttf"

try:
    font = ImageFont.truetype(font_path, 32)
except IOError:
    print(f"Không tìm thấy font tại {font_path}. Sử dụng font mặc định.")
    font = ImageFont.load_default()

# Ánh xạ cảm xúc thành giá trị số
emotion_values = {
    'Angry': -3,
    'Disgusted': -2,
    'Fear': -1,
    'Happy': 3,
    'Sad': -2,
    'Surprised': 2,
    'Neutral': 0
}

# Đảo ngược ánh xạ từ giá trị về cảm xúc
reverse_emotion_values = {v: k for k, v in emotion_values.items()}

# Hàm tăng sáng và độ tương phản
def adjust_gamma(image, gamma=1.5):
    invGamma = 1.0 / gamma
    table = np.array([(i / 255.0) ** invGamma * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

def apply_clahe(gray_image):
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray_image)

# Biến lưu trữ cảm xúc và thời gian
emotion_history = deque(maxlen=30)  # Lưu tối đa 30 giá trị (30 khung hình/giây)
last_sent_time = time.time()
last_sent_emotion = None  # Cảm xúc cuối cùng đã gửi

# Mở webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Không thể mở webcam")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Không đọc được khung hình")
        break

    # Tăng sáng và chuyển đổi ảnh xám
    frame = adjust_gamma(frame, gamma=1.5)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = apply_clahe(gray)

    # Phát hiện khuôn mặt
    faces = face_classifier.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
    for (x, y, w, h) in faces:
        # Vẽ hình chữ nhật quanh khuôn mặt
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

        # Xử lý khuôn mặt để đưa vào mô hình
        roi_gray = gray[y:y + h, x:x + w]
        roi_gray = cv2.resize(roi_gray, (48, 48), interpolation=cv2.INTER_AREA)
        roi = roi_gray.astype('float') / 255.0
        roi = img_to_array(roi)
        roi = np.expand_dims(roi, axis=0)

        # Dự đoán cảm xúc
        preds = classifier.predict(roi, verbose=0)[0]
        label = class_labels[np.argmax(preds)]

        # Gán giá trị cảm xúc và lưu vào lịch sử
        emotion_value = emotion_values.get(label, 0)
        emotion_history.append(emotion_value)

        # Vẽ nhãn cảm xúc lên khung hình
        img_pil = Image.fromarray(frame)
        draw = ImageDraw.Draw(img_pil)
        draw.text((x, y - 40), label, font=font, fill=(0, 255, 0, 0))
        frame = np.array(img_pil)

    # Gửi dữ liệu cảm xúc mỗi 1 giây
    current_time = time.time()
    if current_time - last_sent_time >= 1:  # Kiểm tra sau mỗi 1 giây
        if len(emotion_history) > 0:
            average_emotion = sum(emotion_history) / len(emotion_history)
            rounded_emotion = round(average_emotion)  # Làm tròn giá trị
            final_emotion = reverse_emotion_values.get(rounded_emotion, "Unknown")  # Ánh xạ về cảm xúc

            # Chỉ gửi nếu không phải "Unknown" và cảm xúc thay đổi
            if final_emotion != "Unknown" and final_emotion != last_sent_emotion:
                # Tạo JSON và gửi qua MQTT
                emotion_data = {
                    "source": "ai",
                    "type": "emotion",
                    "emotion": final_emotion
                }
                client.publish(TOPIC, json.dumps(emotion_data))
                print(f"Sent emotion data: {emotion_data}")

                # Cập nhật cảm xúc đã gửi
                last_sent_emotion = final_emotion
        last_sent_time = current_time

    # Hiển thị khung hình
    cv2.imshow('Emotion Detection - Multi-Face', frame)

    # Thoát khi nhấn 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
client.disconnect()
