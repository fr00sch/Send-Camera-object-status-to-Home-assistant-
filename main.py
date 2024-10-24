from ultralytics import YOLOWorld
import cv2
import numpy as np
import requests
import json
import paho.mqtt.client as mqtt
import base64
import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Retrieve the MQTT broker information from the environment variables
MQTT_BROKER = os.getenv('MQTT_BROKER')
MQTT_PORT = int(os.getenv('MQTT_PORT'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC')
MQTT_TOPIC_IMAGE = os.getenv('MQTT_TOPIC_IMAGE')

# Define the path where the model will be stored
model_path = "downloads/yolov8x-worldv2.pt"

# Define the URL from which to download the model if it doesn't exist
download_url = "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8x-worldv2.pt"

# Check if the file already exists
if not os.path.exists(model_path):
    # If it doesn't exist, download it from the specified URL
    response = requests.get(download_url)
    
    # Save the downloaded content to the local file
    with open(model_path, "wb") as f:
        f.write(response.content)
    
    print(f"File {model_path} not found and has been downloaded from {download_url}")
else:
    print(f"File {model_path} already exists.")

# Laden des Modells
model = YOLOWorld(model_path)

# Definieren der spezifischen Mülltonnen-Klassen
classes = ['garbage bin']
model.set_classes(classes)

# Definition der Zonen (in Prozent des Bildes)
# Format: (x_start, y_start, x_end, y_end)
ZONE = (0.35, 0.2, 0.7, 0.6)  # Beispiel: mittlere 60% des Bildes

def download_image(url):
    response = requests.get(url)
    image = np.array(bytearray(response.content), dtype=np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image

def resize_image(image, target_size=1280):
    h, w = image.shape[:2]
    if h > w:
        new_h, new_w = target_size, int(w * (target_size / h))
    else:
        new_h, new_w = int(h * (target_size / w)), target_size
    return cv2.resize(image, (new_w, new_h))


def send_image_mqtt(image):
    resized_image = resize_image(image)
    _, buffer = cv2.imencode('.jpg', resized_image)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    client.publish(MQTT_TOPIC_IMAGE, jpg_as_text, retain=True)

# Define callback functions
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    print(f"Message received from topic {msg.topic}: {msg.payload}")

def is_in_zone(box, image_shape, zone):
    ih, iw = image_shape[:2]
    x1, y1, x2, y2 = box
    zx1, zy1, zx2, zy2 = [int(z * dim) for z, dim in zip(zone, [iw, ih, iw, ih])]

    # Überprüfen, ob das Zentrum der Box in der Zone liegt
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    return zx1 <= center_x <= zx2 and zy1 <= center_y <= zy2

def non_maximum_suppression(detections, iou_threshold=0.5):
    # Sort detections by score in decreasing order
    detections = sorted(detections, key=lambda x: x[4], reverse=True)
    final_detections = []

    while detections:
        best = detections.pop(0)  # Take the detection with the highest score
        final_detections.append(best)

        def iou(box1, box2):
            # Calculate Intersection-Over-Union (IoU) of two bounding boxes
            x1 = max(box1[0], box2[0])
            y1 = max(box1[1], box2[1])
            x2 = min(box1[2], box2[2])
            y2 = min(box1[3], box2[3])

            inter_area = max(0, x2 - x1) * max(0, y2 - y1)
            box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
            box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
            union_area = box1_area + box2_area - inter_area

            return inter_area / union_area if union_area else 0

        # Remove all detections that have a high IoU with the best detection
        detections = [det for det in detections if iou(best[:4], det[:4]) < iou_threshold]

    return final_detections

# URL des Bildes
image_url = os.getenv('IMAGE_LINK')

# Bild herunterladen und verarbeiten
image = download_image(image_url)
results = model(image)

# Zähler für jeden Mülltonnen-Typ initialisieren
bin_counts = {cls: 0 for cls in classes}

# Verarbeiten der Ergebnisse
detections = results[0].boxes.data

# Apply non-maximum suppression
detections = non_maximum_suppression(detections)

# Zähler für jeden Mülltonnen-Typ initialisieren
bin_counts = {cls: 0 for cls in classes}

for detection in detections:
    x1, y1, x2, y2, score, class_id = detection
    if score > 0.5 and is_in_zone((x1, y1, x2, y2), image.shape, ZONE):
        label = classes[int(class_id)]
        bin_counts[label] += 1
        
        # Optional: Zeichnen der erkannten Mülltonnen und der Zone
        cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(image, f'{label}: {score:.2f}', (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

# Zone zeichnen
ih, iw = image.shape[:2]
zx1, zy1, zx2, zy2 = [int(z * dim) for z, dim in zip(ZONE, [iw, ih, iw, ih])]
cv2.rectangle(image, (zx1, zy1), (zx2, zy2), (255, 0, 0), 2)

try:
    # Bild anzeigen
    cv2.imshow('Detected Garbage Bins in Zone', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
except Exception as e:
    print(e)

# Ergebnisse vorbereiten
total_bins = sum(bin_counts.values())
found_bins = [bin_type for bin_type, count in bin_counts.items() if count > 0]
missing_bins = list(set(classes) - set(found_bins))

result = {
    "total_bins_in_zone": total_bins,
    "detected_bins_in_zone": bin_counts,
    "found_bins_in_zone": found_bins,
    "missing_bins_in_zone": missing_bins
}

# Create an MQTT client instance
client = mqtt.Client()

# Assign the callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Start the loop to process received messages and maintain the connection
client.loop_start()

# Ergebnisse als JSON-String formatieren und senden
json_result = json.dumps(result)
client.publish(MQTT_TOPIC, json_result, retain=True)

# Bild senden
send_image_mqtt(image)

# Use loop_stop() when you want to stop processing and disconnect
client.loop_stop()
client.disconnect()

print(f"Ergebnisse gesendet: {json_result}")
