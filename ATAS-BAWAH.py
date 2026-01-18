import cv2
import serial
import time

# ===== KONFIGURASI =====
PORT = 'COM10'
BAUD = 9600
CAM_INDEX = 0
CENTER_TOL = 80        # zona tengah vertikal
SEND_INTERVAL = 0.3
# ======================

# Serial
ser = serial.Serial(PORT, BAUD)
time.sleep(2)

# Kamera
cap = cv2.VideoCapture(CAM_INDEX)

# Haar cascade face
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

last_send = 0
last_cmd = None

print("Face tracking ATAS–BAWAH started. Press Q to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    h, w = frame.shape[:2]
    center_y = h // 2   # 🔥 TENGAH VERTIKAL

    cmd = 'C'  # STOP

    if len(faces) > 0:
        # Ambil wajah pertama
        x, y, fw, fh = faces[0]
        face_center = y + fh // 2   # 🔥 PUSAT WAJAH Y

        # ===== LOGIKA ATAS / TENGAH / BAWAH =====
        if face_center < center_y - CENTER_TOL:
            cmd = 'T'   # ATAS
        elif face_center > center_y + CENTER_TOL:
            cmd = 'D'   # BAWAH
        else:
            cmd = 'C'

        # Kotak wajah
        cv2.rectangle(frame, (x, y), (x + fw, y + fh), (0, 255, 0), 2)

        # Garis tengah wajah (HORIZONTAL)
        cv2.line(frame, (0, face_center), (w, face_center), (255, 0, 0), 1)

    # ===== GARIS VISUAL =====

    # Garis tengah kamera (MERAH)
    cv2.line(frame, (0, center_y), (w, center_y), (0, 0, 255), 2)

    # Batas zona tengah (KUNING)
    cv2.line(frame, (0, center_y - CENTER_TOL),
             (w, center_y - CENTER_TOL), (0, 255, 255), 2)
    cv2.line(frame, (0, center_y + CENTER_TOL),
             (w, center_y + CENTER_TOL), (0, 255, 255), 2)

    # Status
    cv2.putText(
        frame,
        f"CMD: {cmd}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    # ===== KIRIM KE ARDUINO =====
    now = time.time()
    if cmd != last_cmd or (now - last_send) > SEND_INTERVAL:
        ser.write(cmd.encode())
        last_cmd = cmd
        last_send = now

    cv2.imshow("Face Tracking Servo 360 (VERTIKAL)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
ser.close()
