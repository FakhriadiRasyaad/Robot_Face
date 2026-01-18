# import cv2
# import serial
# import time

# # ===== KONFIGURASI =====
# PORT = 'COM10'
# BAUD = 9600
# CAM_INDEX = 0

# CENTER_TOL_X = 80   # toleransi kiri-kanan
# CENTER_TOL_Y = 80   # toleransi atas-bawah

# SEND_INTERVAL = 0.3
# # ======================

# # Serial
# ser = serial.Serial(PORT, BAUD)
# time.sleep(2)

# # Kamera
# cap = cv2.VideoCapture(CAM_INDEX)

# # Haar cascade
# face_cascade = cv2.CascadeClassifier(
#     cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
# )

# last_send = 0
# last_cmd = None

# print("Face tracking 2 AXIS started. Press Q to quit.")

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     faces = face_cascade.detectMultiScale(gray, 1.3, 5)

#     h, w = frame.shape[:2]
#     center_x = w // 2
#     center_y = h // 2

#     cmd = 'C'  # default STOP

#     if len(faces) > 0:
#         # 🔥 ambil wajah TERBESAR biar stabil
#         x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])

#         face_center_x = x + fw // 2
#         face_center_y = y + fh // 2

#         # ===== PRIORITAS VERTIKAL =====
#         if face_center_y < center_y - CENTER_TOL_Y:
#             cmd = 'T'
#         elif face_center_y > center_y + CENTER_TOL_Y:
#             cmd = 'D'
#         # ===== BARU CEK HORIZONTAL =====
#         elif face_center_x < center_x - CENTER_TOL_X:
#             cmd = 'L'
#         elif face_center_x > center_x + CENTER_TOL_X:
#             cmd = 'R'
#         else:
#             cmd = 'C'

#         # ===== VISUAL WAJAH =====
#         cv2.rectangle(frame, (x, y), (x + fw, y + fh), (0, 255, 0), 2)

#         # garis tengah wajah
#         cv2.line(frame, (face_center_x, 0), (face_center_x, h), (255, 0, 0), 1)
#         cv2.line(frame, (0, face_center_y), (w, face_center_y), (255, 0, 0), 1)

#     # ===== GARIS REFERENSI =====

#     # tengah kamera
#     cv2.line(frame, (center_x, 0), (center_x, h), (0, 0, 255), 2)
#     cv2.line(frame, (0, center_y), (w, center_y), (0, 0, 255), 2)

#     # zona tengah X
#     cv2.line(frame, (center_x - CENTER_TOL_X, 0),
#              (center_x - CENTER_TOL_X, h), (0, 255, 255), 2)
#     cv2.line(frame, (center_x + CENTER_TOL_X, 0),
#              (center_x + CENTER_TOL_X, h), (0, 255, 255), 2)

#     # zona tengah Y
#     cv2.line(frame, (0, center_y - CENTER_TOL_Y),
#              (w, center_y - CENTER_TOL_Y), (0, 255, 255), 2)
#     cv2.line(frame, (0, center_y + CENTER_TOL_Y),
#              (w, center_y + CENTER_TOL_Y), (0, 255, 255), 2)

#     # status
#     cv2.putText(frame, f"CMD: {cmd}", (20, 40),
#                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

#     # ===== KIRIM KE ARDUINO =====
#     now = time.time()
#     if cmd != last_cmd or (now - last_send) > SEND_INTERVAL:
#         ser.write(cmd.encode())
#         last_cmd = cmd
#         last_send = now

#     cv2.imshow("Face Tracking Dual Servo (2 Axis)", frame)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# # Cleanup
# cap.release()
# cv2.destroyAllWindows()
# ser.write(b'C')
# ser.close()
# ===================================================================
import cv2
import serial
import time
import mediapipe as mp

# ===== KONFIGURASI =====
PORT = 'COM10'
BAUD = 9600
CAM_INDEX = 0

CENTER_TOL_X = 80   # toleransi kiri-kanan
CENTER_TOL_Y = 80   # toleransi atas-bawah

SEND_INTERVAL = 0.3
# ======================

# Serial
ser = serial.Serial(PORT, BAUD)
time.sleep(2)

# Kamera
cap = cv2.VideoCapture(CAM_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Haar cascade untuk face tracking
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# MediaPipe untuk hand tracking (HANYA COUNTING)
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.3,
    model_complexity=1
)

last_send = 0
last_cmd = None

def count_fingers(hand_landmarks, handedness):
    """
    Menghitung jumlah jari yang terangkat
    """
    finger_tips = [
        mp_hands.HandLandmark.THUMB_TIP,
        mp_hands.HandLandmark.INDEX_FINGER_TIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        mp_hands.HandLandmark.RING_FINGER_TIP,
        mp_hands.HandLandmark.PINKY_TIP
    ]
    
    finger_pips = [
        mp_hands.HandLandmark.THUMB_IP,
        mp_hands.HandLandmark.INDEX_FINGER_PIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
        mp_hands.HandLandmark.RING_FINGER_PIP,
        mp_hands.HandLandmark.PINKY_PIP
    ]
    
    finger_mcps = [
        mp_hands.HandLandmark.THUMB_CMC,
        mp_hands.HandLandmark.INDEX_FINGER_MCP,
        mp_hands.HandLandmark.MIDDLE_FINGER_MCP,
        mp_hands.HandLandmark.RING_FINGER_MCP,
        mp_hands.HandLandmark.PINKY_MCP
    ]
    
    count = 0
    fingers_up = []
    
    is_right_hand = handedness == "Right"
    
    for i in range(5):
        tip = hand_landmarks.landmark[finger_tips[i]]
        pip = hand_landmarks.landmark[finger_pips[i]]
        mcp = hand_landmarks.landmark[finger_mcps[i]]
        
        # JEMPOL (horizontal check)
        if i == 0:
            if is_right_hand:
                if tip.x < pip.x - 0.04:
                    count += 1
                    fingers_up.append(True)
                else:
                    fingers_up.append(False)
            else:
                if tip.x > pip.x + 0.04:
                    count += 1
                    fingers_up.append(True)
                else:
                    fingers_up.append(False)
        
        # JARI LAINNYA (vertical check)
        else:
            if tip.y < pip.y and pip.y < mcp.y:
                count += 1
                fingers_up.append(True)
            else:
                fingers_up.append(False)
    
    return count, fingers_up

print("🎮 FACE TRACKING + FINGER COUNTING SYSTEM")
print("=" * 60)
print("✅ Face Tracking: Controls Servo (Active)")
print("✅ Hand Tracking: Counts Fingers ONLY (Display Only)")
print("Press Q to Quit")
print("=" * 60)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]
    center_x = w // 2
    center_y = h // 2

    cmd = 'C'  # default STOP

    # ===== FACE TRACKING (KONTROL SERVO) =====
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    face_detected = False
    if len(faces) > 0:
        face_detected = True
        # Ambil wajah TERBESAR
        x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])

        face_center_x = x + fw // 2
        face_center_y = y + fh // 2

        # PRIORITAS VERTIKAL
        if face_center_y < center_y - CENTER_TOL_Y:
            cmd = 'T'
        elif face_center_y > center_y + CENTER_TOL_Y:
            cmd = 'D'
        # CEK HORIZONTAL
        elif face_center_x < center_x - CENTER_TOL_X:
            cmd = 'L'
        elif face_center_x > center_x + CENTER_TOL_X:
            cmd = 'R'
        else:
            cmd = 'C'

        # Visual wajah
        cv2.rectangle(frame, (x, y), (x + fw, y + fh), (0, 255, 0), 2)
        cv2.line(frame, (face_center_x, 0), (face_center_x, h), (255, 0, 0), 1)
        cv2.line(frame, (0, face_center_y), (w, face_center_y), (255, 0, 0), 1)

    # ===== HAND TRACKING (HANYA COUNTING) =====
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    hand_info = "NO HAND"
    finger_count = 0
    
    if results.multi_hand_landmarks and results.multi_handedness:
        # Proses semua tangan yang terdeteksi
        for idx, (hand_landmarks, handedness_info) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
            handedness = handedness_info.classification[0].label
            
            # Gambar skeleton tangan
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

            # Hitung jari
            finger_count, fingers_up = count_fingers(hand_landmarks, handedness)

            # Dapatkan posisi wrist untuk display
            wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
            wrist_x = int(wrist.x * w)
            wrist_y = int(wrist.y * h)

            # Background untuk text jumlah jari
            text = f"{finger_count}"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 3, 5)[0]
            
            # Rectangle background
            bg_x1 = wrist_x - text_size[0] // 2 - 30
            bg_y1 = wrist_y - text_size[1] - 40
            bg_x2 = wrist_x + text_size[0] // 2 + 30
            bg_y2 = wrist_y - 10
            
            cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)
            cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 255, 255), 3)
            
            # Tampilkan angka jumlah jari
            cv2.putText(frame, text,
                       (wrist_x - text_size[0] // 2, wrist_y - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 255), 5)

            # Label tangan (Right/Left)
            hand_label = f"{handedness}"
            cv2.putText(frame, hand_label,
                       (wrist_x - 40, wrist_y + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            hand_info = f"{handedness}: {finger_count} JARI"

    # ===== GARIS REFERENSI (untuk face tracking) =====
    # Tengah kamera
    cv2.line(frame, (center_x, 0), (center_x, h), (0, 0, 255), 2)
    cv2.line(frame, (0, center_y), (w, center_y), (0, 0, 255), 2)

    # Zona tengah X
    cv2.line(frame, (center_x - CENTER_TOL_X, 0),
             (center_x - CENTER_TOL_X, h), (0, 255, 255), 1)
    cv2.line(frame, (center_x + CENTER_TOL_X, 0),
             (center_x + CENTER_TOL_X, h), (0, 255, 255), 1)

    # Zona tengah Y
    cv2.line(frame, (0, center_y - CENTER_TOL_Y),
             (w, center_y - CENTER_TOL_Y), (0, 255, 255), 1)
    cv2.line(frame, (0, center_y + CENTER_TOL_Y),
             (w, center_y + CENTER_TOL_Y), (0, 255, 255), 1)

    # ===== STATUS DISPLAY =====
    # Background top panel
    cv2.rectangle(frame, (0, 0), (w, 120), (0, 0, 0), -1)
    cv2.rectangle(frame, (0, 0), (w, 120), (0, 255, 0), 2)
    
    # FACE TRACKING STATUS (kiri)
    face_status = "DETECTED" if face_detected else "NO FACE"
    face_color = (0, 255, 0) if face_detected else (0, 0, 255)
    
    cv2.putText(frame, "FACE TRACKING:", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, face_status, (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1, face_color, 2)
    cv2.putText(frame, f"CMD: {cmd}", (20, 105),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    
    # HAND COUNTING STATUS (kanan)
    cv2.putText(frame, "FINGER COUNT:", (w - 350, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, hand_info, (w - 350, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    # Bottom info
    cv2.rectangle(frame, (0, h - 50), (w, h), (0, 0, 0), -1)
    cv2.putText(frame, "SERVO: Controlled by FACE | HAND: Display Only (No Servo Control)", 
                (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # ===== KIRIM KE ARDUINO (HANYA DARI FACE TRACKING) =====
    now = time.time()
    if cmd != last_cmd or (now - last_send) > SEND_INTERVAL:
        ser.write(cmd.encode())
        last_cmd = cmd
        last_send = now
        print(f"📡 Servo CMD: {cmd} | Face: {face_status} | Hand: {hand_info}")

    cv2.imshow("Face Tracking (Servo) + Finger Counting (Display)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
ser.write(b'C')
ser.close()
hands.close()
print("\n✅ Program terminated")




# ====================================================================
# import cv2
# import serial
# import time
# import mediapipe as mp

# # ===== KONFIGURASI =====
# PORT = 'COM10'
# BAUD = 9600
# CAM_INDEX = 0

# CENTER_TOL_X = 80
# CENTER_TOL_Y = 80
# SEND_INTERVAL = 0.3
# # ======================

# # ===== SERIAL =====
# ser = serial.Serial(PORT, BAUD)
# time.sleep(2)

# # ===== CAMERA =====
# cap = cv2.VideoCapture(CAM_INDEX)

# # ===== FACE DETECTOR =====
# face_cascade = cv2.CascadeClassifier(
#     cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
# )

# # ===== MEDIAPIPE HANDS =====
# mp_hands = mp.solutions.hands
# mp_draw = mp.solutions.drawing_utils
# hands = mp_hands.Hands(
#     static_image_mode=False,
#     max_num_hands=1,
#     min_detection_confidence=0.6,
#     min_tracking_confidence=0.6
# )

# # ===== STATE =====
# last_send = 0
# last_cmd = None
# last_fingers = None

# print("Face + Hand Tracking started. Press Q to quit.")

# def count_fingers(hand_landmarks):
#     """
#     Hitung jumlah jari (1–5)
#     """
#     fingers = 0

#     # Thumb (horizontal)
#     if hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x:
#         fingers += 1

#     # Index, Middle, Ring, Pinky (vertical)
#     tips = [8, 12, 16, 20]
#     pips = [6, 10, 14, 18]

#     for tip, pip in zip(tips, pips):
#         if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
#             fingers += 1

#     return fingers

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     h, w = frame.shape[:2]
#     center_x, center_y = w // 2, h // 2

#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#     faces = face_cascade.detectMultiScale(gray, 1.3, 5)
#     cmd = 'C'

#     # ================= FACE TRACKING =================
#     if len(faces) > 0:
#         x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])

#         face_center_x = x + fw // 2
#         face_center_y = y + fh // 2

#         if face_center_y < center_y - CENTER_TOL_Y:
#             cmd = 'T'
#         elif face_center_y > center_y + CENTER_TOL_Y:
#             cmd = 'D'
#         elif face_center_x < center_x - CENTER_TOL_X:
#             cmd = 'L'
#         elif face_center_x > center_x + CENTER_TOL_X:
#             cmd = 'R'
#         else:
#             cmd = 'C'

#         cv2.rectangle(frame, (x, y), (x + fw, y + fh), (0, 255, 0), 2)
#         cv2.line(frame, (face_center_x, 0), (face_center_x, h), (255, 0, 0), 1)
#         cv2.line(frame, (0, face_center_y), (w, face_center_y), (255, 0, 0), 1)

#     # ================= HAND DETECTION =================
#     result = hands.process(rgb)
#     finger_count = 0

#     if result.multi_hand_landmarks:
#         for hand_landmarks in result.multi_hand_landmarks:
#             finger_count = count_fingers(hand_landmarks)

#             mp_draw.draw_landmarks(
#                 frame,
#                 hand_landmarks,
#                 mp_hands.HAND_CONNECTIONS
#             )

#     # ================= UI =================
#     cv2.line(frame, (center_x, 0), (center_x, h), (0, 0, 255), 2)
#     cv2.line(frame, (0, center_y), (w, center_y), (0, 0, 255), 2)

#     cv2.putText(frame, f"CMD: {cmd}", (20, 40),
#                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

#     cv2.putText(frame, f"FINGERS: {finger_count}", (20, 80),
#                 cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

#     # ================= SERIAL SEND =================
#     now = time.time()

#     if cmd != last_cmd or (now - last_send) > SEND_INTERVAL:
#         ser.write(cmd.encode())
#         last_cmd = cmd
#         last_send = now

#     # kirim jumlah jari (optional)
#     if finger_count != last_fingers:
#         ser.write(str(finger_count).encode())  # kirim '0'–'5'
#         last_fingers = finger_count

#     cv2.imshow("Face + Hand Tracking", frame)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# # ===== CLEANUP =====
# cap.release()
# cv2.destroyAllWindows()
# ser.write(b'C')
# ser.close()
