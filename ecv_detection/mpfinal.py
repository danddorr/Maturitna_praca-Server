import cv2
import numpy as np
import time
from datetime import datetime
from paddleocr import PaddleOCR
from ultralytics import YOLO
import websocket

blocked_ecvs = {}


CAMERA1_URL = "rtsp://10.0.16.2:7447/zI0beKFiX41fGOPQ"
#CAMERA2_URL = "########################################"

"""vcap = cv2.VideoCapture(CAMERA1_URL)
while(1):
    ret, frame = vcap.read()
    cv2.imshow('VIDEO', frame)
    cv2.waitKey(1)

exit()"""


def hladanie(cam, model):
    threshold = 0.5
    ret, frame = cam.read()
    if not ret:
        print("Failed to retrieve frame from camera")
        return None
        
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = model.predict(frame_rgb)[0]
    for result in results.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = result
        if score > threshold:
            class_name = results.names[int(class_id)].lower()
            if class_name == "plate":
                plate_crop = frame[int(y1):int(y2), int(x1):int(x2)]
                return plate_crop
    return None

def send_text_via_websocket(cleaned_text, camera_position):
    global blocked_ecvs
    cleaned_text = cleaned_text.replace("-", "")

    if cleaned_text in blocked_ecvs and time.time() < blocked_ecvs[cleaned_text]:
        #print(f"Skipping {cleaned_text} (blocked for 15s)")
        return
    
    with open("ecv_detection.log", "a") as file:
        file.write(f"{datetime.strftime(datetime.now(), '%Y-%m-%d, %H:%M:%S')} - {camera_position} - {cleaned_text}\n")

    try:
        ws = websocket.create_connection("wss://mp.seatbook.sk/ws/gate/?special_token=kvFcUmBUUT18s9Ig7W37SCWgFVq7QW-_RJPPytWYgej8-5GmBGPDFdrZAeNL2I3Q")
        ws.recv()
        message = f'{{"type":"ecv_detected", "camera_position":"{camera_position}", "message":"{cleaned_text}"}}'
        ws.send(message)
        print(f"Sent via WebSocket: {cleaned_text} from {camera_position}")

        response = ws.recv()
        print(f"Server Response: {response}")

        if '{"type": "error", "message": "Ecv not registered"}' in response:
            blocked_ecvs[cleaned_text] = time.time() + 15
        elif '{"type": "success", "message": "Triggered"}' in response:
            print("Gate trigger success")
            blocked_ecvs[cleaned_text] = time.time() + 15

        ws.close()
    except Exception as e:
        print(f"WebSocket error: {e}")

def process_camera(camera, camera_position, model, ocr, last_sent_time):
    plate_crop = hladanie(camera, model)
    if plate_crop is not None:
        gray_plate = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        results = ocr.ocr(gray_plate, cls=True)

        if results and isinstance(results, list):
            for line in results:
                if line:
                    for word_info in line:
                        if len(word_info) >= 2:
                            text = word_info[1][0]

                            if time.time() - last_sent_time[camera_position] >= 0.5:
                                send_text_via_websocket(text, camera_position)
                                last_sent_time[camera_position] = time.time()
                                print(f"Recognized Plate: {text} from {camera_position}")

def main():
    model = YOLO("last.pt")
    ocr = PaddleOCR(use_angle_cls=True, lang='en')

    
    kamera1 = cv2.VideoCapture(CAMERA1_URL)
    #kamera2 = cv2.VideoCapture(CAMERA2_URL)
    
    
    kamera1.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    kamera1.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    #kamera2.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    #kamera2.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    
    if not kamera1.isOpened():# or not kamera2.isOpened():
        print("Error: Could not open one or more cameras.")
        return

    last_sent_time = {"outside": 0, "inside": 0}

    while True:
        process_camera(kamera1, "inside", model, ocr, last_sent_time)
        #process_camera(kamera2, "outside", model, ocr, last_sent_time)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        time.sleep(0.5)

    cv2.destroyAllWindows()
    kamera1.release()
    #kamera2.release()

if __name__ == "__main__":
    main()