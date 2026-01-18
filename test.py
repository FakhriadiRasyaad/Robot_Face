import serial
import time
from pynput import keyboard

#test WASD

# ===== KONFIGURASI =====
PORT = 'COM10'
BAUD = 9600
SEND_INTERVAL = 0.15   # detik (anti spam)
# ======================

# Serial
ser = serial.Serial(PORT, BAUD)
time.sleep(2)

current_cmd = 'C'
last_cmd = None
last_send = 0

print("SERVO 360 MANUAL CONTROL")
print("W = ATAS | S = BAWAH | A = KIRI | D = KANAN | ESC = EXIT")

def send_cmd(cmd):
    global last_cmd, last_send
    now = time.time()
    if cmd != last_cmd or (now - last_send) > SEND_INTERVAL:
        ser.write(cmd.encode())
        last_cmd = cmd
        last_send = now
        print("CMD:", cmd)

def on_press(key):
    global current_cmd
    try:
        k = key.char.lower()
        if k == 'w':
            current_cmd = 'T'
        elif k == 's':
            current_cmd = 'D'
        elif k == 'a':
            current_cmd = 'L'
        elif k == 'd':
            current_cmd = 'R'
    except AttributeError:
        if key == keyboard.Key.esc:
            ser.write(b'C')
            ser.close()
            return False

def on_release(key):
    global current_cmd
    try:
        if key.char.lower() in ['w', 'a', 's', 'd']:
            current_cmd = 'C'
    except AttributeError:
        pass

# Keyboard listener
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

# Loop kirim command
try:
    while listener.running:
        send_cmd(current_cmd)
        time.sleep(0.05)
except KeyboardInterrupt:
    pass

# Cleanup
ser.write(b'C')
ser.close()
