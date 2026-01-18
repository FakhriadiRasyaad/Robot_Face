import cv2
import serial
import time

# ===== SERIAL =====
ser = serial.Serial('COM10', 9600, timeout=1)
time.sleep(2)

# ===== FACE DETECTOR =====
face = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

cap = cv2.VideoCapture(0)

last_zone = None  # supaya tidak spam servo

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    center_frame = w // 2

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face.detectMultiScale(gray, 1.3, 5)

    for (x, y, fw, fh) in faces:
        face_center_x = x + fw // 2

        # ===== ZONE DETECTION =====
        if face_center_x < w * 0.4:
            zone = "LEFT"
            angle = 30
        elif face_center_x > w * 0.6:
            zone = "RIGHT"
            angle = 150
        else:
            zone = "CENTER"
            angle = 90

        # ===== SEND ONLY IF CHANGED =====
        if zone != last_zone:
            ser.write(f"{angle}\n".encode())
            print(f"{zone} → SERVO {angle}")
            last_zone = zone

        # ===== DRAW =====
        cv2.rectangle(frame, (x,y), (x+fw,y+fh), (0,255,0), 2)
        cv2.line(frame, (center_frame, 0), (center_frame, h), (255,0,0), 2)
        cv2.putText(frame, zone, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,255), 2)

    cv2.imshow("Face Direction Servo", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
ser.close()
cv2.destroyAllWindows()
