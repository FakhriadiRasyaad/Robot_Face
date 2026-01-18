"""
Face Tracking - LIMITED RANGE
Servo hanya bergerak 45° - 135° (total 90°)
"""

import cv2
import mediapipe as mp
import serial
import time
import numpy as np

# ========================
# KONFIGURASI
# ========================
SERIAL_PORT = 'COM11'  # <<< SESUAIKAN!
BAUD_RATE = 115200

FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Dead zone
DEAD_ZONE = 80

# SERVO LIMITS - HANYA 90 DERAJAT
SERVO_MIN = 45      # Kiri maksimal
SERVO_CENTER = 90   # Tengah
SERVO_MAX = 135     # Kanan maksimal

print("\n" + "="*60)
print(f"SERVO RANGE: {SERVO_MIN}° - {SERVO_MAX}° (total {SERVO_MAX - SERVO_MIN}°)")
print("="*60)

# ========================
# INISIALISASI
# ========================
mp_face_detection = mp.solutions.face_detection
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

face_detection = mp_face_detection.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.5
)

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

cap = cv2.VideoCapture(2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

# Connect Arduino
try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    
    while arduino.in_waiting:
        print(arduino.readline().decode().strip())
    
    print(f"\n✓ Connected")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    exit(1)

# ========================
# VARIABLES
# ========================
servo_angle = SERVO_CENTER
tracking_active = False

last_hand_state = None
state_cooldown = 0
COOLDOWN_FRAMES = 15

angle_history = [SERVO_CENTER] * 5

# ========================
# FUNCTIONS
# ========================

def is_hand_open(landmarks):
    """Deteksi tangan terbuka/mengepal"""
    tips = [8, 12, 16, 20]
    mcps = [5, 9, 13, 17]
    wrist = landmarks.landmark[0]
    
    fingers_up = 0
    for tip_id, mcp_id in zip(tips, mcps):
        tip = landmarks.landmark[tip_id]
        mcp = landmarks.landmark[mcp_id]
        
        tip_dist = np.sqrt((tip.x - wrist.x)**2 + (tip.y - wrist.y)**2)
        mcp_dist = np.sqrt((mcp.x - wrist.x)**2 + (mcp.y - wrist.y)**2)
        
        if tip_dist > mcp_dist:
            fingers_up += 1
    
    return fingers_up >= 3

def calculate_angle(face_x):
    """
    Hitung angle servo dari posisi wajah
    Range terbatas: 45° - 135°
    """
    center_x = FRAME_WIDTH // 2
    offset = face_x - center_x
    
    # Dead zone
    if abs(offset) < DEAD_ZONE:
        return SERVO_CENTER
    
    # Map face X position ke servo angle
    # Wajah KIRI (x=0) → Servo 135° (kanan servo = kiri kamera)
    # Wajah KANAN (x=640) → Servo 45° (kiri servo = kanan kamera)
    angle = np.interp(face_x, [0, FRAME_WIDTH], [SERVO_MAX, SERVO_MIN])
    
    # HARD LIMIT dalam range
    angle = np.clip(angle, SERVO_MIN, SERVO_MAX)
    
    return int(angle)

def send_command(angle, status):
    """Kirim ke Arduino dengan HARD LIMIT"""
    # Double check limit sebelum kirim
    angle = int(np.clip(angle, SERVO_MIN, SERVO_MAX))
    
    if arduino and arduino.is_open:
        try:
            cmd = f"{angle},{status}\n"
            arduino.write(cmd.encode())
            arduino.flush()
        except Exception as e:
            print(f"Send error: {e}")

# ========================
# MAIN LOOP
# ========================

print("\nCONTROLS:")
print("  ✋ Open hand  → START tracking")
print("  ✊ Close fist → STOP")
print("  Q           → Quit")
print("="*60 + "\n")

# Set awal ke center
send_command(SERVO_CENTER, 0)
time.sleep(0.5)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # ========================
    # HAND GESTURE
    # ========================
    hand_result = hands.process(rgb)
    current_state = None
    
    if hand_result.multi_hand_landmarks:
        for hand_landmarks in hand_result.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2),
                mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
            )
            
            is_open = is_hand_open(hand_landmarks)
            current_state = 'open' if is_open else 'closed'
    
    # TOGGLE
    if state_cooldown > 0:
        state_cooldown -= 1
    
    if current_state and state_cooldown == 0:
        if current_state != last_hand_state:
            if current_state == 'open' and last_hand_state == 'closed':
                tracking_active = True
                print("🟢 TRACKING ON")
                state_cooldown = COOLDOWN_FRAMES
                
            elif current_state == 'closed' and last_hand_state == 'open':
                tracking_active = False
                print(f"🔴 TRACKING OFF (at {servo_angle}°)")
                state_cooldown = COOLDOWN_FRAMES
            
            last_hand_state = current_state
    
    # ========================
    # FACE DETECTION
    # ========================
    face_result = face_detection.process(rgb)
    
    if face_result.detections:
        for detection in face_result.detections:
            bbox = detection.location_data.relative_bounding_box
            h, w, _ = frame.shape
            
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            box_w = int(bbox.width * w)
            box_h = int(bbox.height * h)
            
            face_x = x + box_w // 2
            face_y = y + box_h // 2
            
            # Draw
            color = (0, 255, 0) if tracking_active else (100, 100, 100)
            cv2.rectangle(frame, (x, y), (x + box_w, y + box_h), color, 2)
            cv2.circle(frame, (face_x, face_y), 5, (0, 0, 255), -1)
            
            # Calculate angle dengan LIMIT
            new_angle = calculate_angle(face_x)
            
            # Smooth
            angle_history.append(new_angle)
            angle_history.pop(0)
            servo_angle = int(np.mean(angle_history))
            
            # EXTRA SAFETY - limit lagi
            servo_angle = int(np.clip(servo_angle, SERVO_MIN, SERVO_MAX))
            
            # Visual feedback
            cv2.line(frame, (face_x, face_y),
                    (FRAME_WIDTH // 2, face_y), (255, 0, 255), 2)
    
    # ========================
    # SEND TO ARDUINO
    # ========================
    status = 1 if tracking_active else 0
    send_command(servo_angle, status)
    
    # ========================
    # UI DISPLAY
    # ========================
    # Status box
    status_color = (0, 255, 0) if tracking_active else (0, 0, 255)
    cv2.rectangle(frame, (5, 5), (300, 120), (0, 0, 0), -1)
    cv2.rectangle(frame, (5, 5), (300, 120), status_color, 2)
    
    status_text = "TRACKING" if tracking_active else "STOPPED"
    cv2.putText(frame, status_text, (15, 35),
               cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
    
    hand_text = f"Hand: {current_state if current_state else 'none'}"
    cv2.putText(frame, hand_text, (15, 65),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    cv2.putText(frame, f"Angle: {servo_angle}°", (15, 95),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    # Range info
    cv2.putText(frame, f"Range: {SERVO_MIN}°-{SERVO_MAX}°", (310, 25),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    # Center line
    cx = FRAME_WIDTH // 2
    cv2.line(frame, (cx, 0), (cx, FRAME_HEIGHT), (0, 255, 255), 2)
    
    # Dead zone
    cv2.rectangle(frame,
                 (cx - DEAD_ZONE, 50),
                 (cx + DEAD_ZONE, FRAME_HEIGHT - 50),
                 (100, 100, 100), 2)
    cv2.putText(frame, "DEAD ZONE", (cx - 50, 70),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
    
    # Servo position indicator (bottom)
    bar_y = FRAME_HEIGHT - 30
    bar_left = 100
    bar_right = FRAME_WIDTH - 100
    bar_center = (bar_left + bar_right) // 2
    
    # Background bar
    cv2.rectangle(frame, (bar_left, bar_y - 5), (bar_right, bar_y + 5), (50, 50, 50), -1)
    
    # Active range (45° - 135°)
    cv2.rectangle(frame, (bar_left, bar_y - 5), (bar_right, bar_y + 5), (255, 255, 255), 2)
    
    # Labels
    cv2.putText(frame, f"{SERVO_MAX}°", (bar_left - 35, bar_y + 5),
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    cv2.putText(frame, f"{SERVO_CENTER}°", (bar_center - 15, bar_y - 15),
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    cv2.putText(frame, f"{SERVO_MIN}°", (bar_right + 10, bar_y + 5),
               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    cv2.putText(frame, "LEFT", (bar_left - 35, bar_y - 15),
               cv2.FONT_HERSHEY_SIMPLEX, 0.35, (100, 200, 255), 1)
    cv2.putText(frame, "RIGHT", (bar_right + 5, bar_y - 15),
               cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 200, 100), 1)
    
    # Current position marker
    marker_x = int(np.interp(servo_angle, [SERVO_MIN, SERVO_MAX], [bar_right, bar_left]))
    cv2.circle(frame, (marker_x, bar_y), 10, (0, 255, 0), -1)
    cv2.circle(frame, (marker_x, bar_y), 10, (255, 255, 255), 2)
    
    # Center marker
    cv2.circle(frame, (bar_center, bar_y), 5, (0, 255, 255), -1)
    
    # Show
    cv2.imshow('Face Tracking - 90° Range', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ========================
# CLEANUP
# ========================
print("\nReturning to center...")

for _ in range(5):
    send_command(SERVO_CENTER, 0)
    time.sleep(0.1)

cap.release()
cv2.destroyAllWindows()
face_detection.close()
hands.close()

if arduino:
    arduino.close()

print("✓ Stopped\n")