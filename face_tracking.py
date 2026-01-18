import cv2
import mediapipe as mp

def get_position_label(cx, cy, width, height):
    """
    Menentukan posisi relatif terhadap tengah frame.
    Hasil: 'KIRI', 'KANAN', 'ATAS', atau 'BAWAH'
    """
    center_x = width // 2
    center_y = height // 2

    dx = cx - center_x
    dy = cy - center_y

    # Jika pergeseran horizontal lebih besar, pakai KIRI/KANAN
    if abs(dx) > abs(dy):
        if dx < 0:
            return "KIRI"
        else:
            return "KANAN"
    else:
        if dy < 0:
            return "ATAS"
        else:
            return "BAWAH"


def main():
    # Buka kamera (0 = default webcam)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Tidak bisa membuka kamera")
        return

    # Load face detector (Haar Cascade bawaan OpenCV)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    # Inisialisasi MediaPipe Hands
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,          # Hanya 1 tangan
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Gagal membaca frame dari kamera")
            break

        # Balikkan frame biar seperti mirror (opsional)
        frame = cv2.flip(frame, 1)

        # Copy untuk proses RGB (mediapipe) dan gray (face)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Ukuran frame dan titik tengah
        h_frame, w_frame, _ = frame.shape
        center_x = w_frame // 2
        center_y = h_frame // 2
        margin = 60  # toleransi supaya tidak terlalu sensitif

        face_direction_text = "Tidak ada wajah"
        hand_position_text = "Tidak ada tangan"

        # =============== DETEKSI WAJAH ===============
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(80, 80)   # minimal ukuran wajah yang dideteksi
        )

        for (x, y, w, h) in faces:
            # Kotak luar (tebal) - hijau
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

            corner_len = int(w * 0.2)

            # kiri atas
            cv2.line(frame, (x, y), (x + corner_len, y), (0, 255, 0), 3)
            cv2.line(frame, (x, y), (x, y + corner_len), (0, 255, 0), 3)

            # kanan atas
            cv2.line(frame, (x + w, y), (x + w - corner_len, y), (0, 255, 0), 3)
            cv2.line(frame, (x + w, y), (x + w, y + corner_len), (0, 255, 0), 3)

            # kiri bawah
            cv2.line(frame, (x, y + h), (x, y + h - corner_len), (0, 255, 0), 3)
            cv2.line(frame, (x, y + h), (x + corner_len, y + h), (0, 255, 0), 3)

            # kanan bawah
            cv2.line(frame, (x + w, y + h), (x + w - corner_len, y + h), (0, 255, 0), 3)
            cv2.line(frame, (x + w, y + h), (x + w, y + h - corner_len), (0, 255, 0), 3)

            # >>> hitung titik tengah wajah
            cx = x + w // 2
            cy = y + h // 2

            # gambar titik tengah wajah (opsional)
            cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

            # >>> tentukan arah relatif terhadap tengah frame
            arah_x = ""
            arah_y = ""

            if cx < center_x - margin:
                arah_x = "KIRI"
            elif cx > center_x + margin:
                arah_x = "KANAN"
            else:
                arah_x = "TENGAH"

            if cy < center_y - margin:
                arah_y = "ATAS"
            elif cy > center_y + margin:
                arah_y = "BAWAH"
            else:
                arah_y = "TENGAH"

            # gabungkan info arah
            if arah_x == "TENGAH" and arah_y == "TENGAH":
                face_direction_text = "WAJAH DI TENGAH"
            elif arah_y == "TENGAH":
                face_direction_text = f"WAJAH: {arah_x}"
            elif arah_x == "TENGAH":
                face_direction_text = f"WAJAH: {arah_y}"
            else:
                face_direction_text = f"WAJAH: {arah_x} - {arah_y}"

            # print ke terminal
            print(f"Posisi wajah: {face_direction_text}")

            # hanya pakai wajah pertama
            break

        # >>> tampilkan arah wajah di layar
        cv2.putText(
            frame,
            face_direction_text,
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA
        )

        # (opsional) gambar garis tengah frame
        cv2.line(frame, (center_x, 0), (center_x, h_frame), (0, 255, 255), 1)
        cv2.line(frame, (0, center_y), (w_frame, center_y), (0, 255, 255), 1)

        # =============== DETEKSI TANGAN ===============
        results = hands.process(frame_rgb)

        if results.multi_hand_landmarks:
            # Ambil hanya tangan pertama
            hand_landmarks = results.multi_hand_landmarks[0]

            # Ambil bounding box dari titik-titik tangan
            x_coords = [lm.x * w_frame for lm in hand_landmarks.landmark]
            y_coords = [lm.y * h_frame for lm in hand_landmarks.landmark]

            x_min, x_max = int(min(x_coords)), int(max(x_coords))
            y_min, y_max = int(min(y_coords)), int(max(y_coords))

            # Kotak tangan - biru
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 3)

            corner_len = int((x_max - x_min) * 0.25)

            # kiri atas
            cv2.line(frame, (x_min, y_min), (x_min + corner_len, y_min), (255, 0, 0), 3)
            cv2.line(frame, (x_min, y_min), (x_min, y_min + corner_len), (255, 0, 0), 3)

            # kanan atas
            cv2.line(frame, (x_max, y_min), (x_max - corner_len, y_min), (255, 0, 0), 3)
            cv2.line(frame, (x_max, y_min), (x_max, y_min + corner_len), (255, 0, 0), 3)

            # kiri bawah
            cv2.line(frame, (x_min, y_max), (x_min, y_max - corner_len), (255, 0, 0), 3)
            cv2.line(frame, (x_min, y_max), (x_min + corner_len, y_max), (255, 0, 0), 3)

            # kanan bawah
            cv2.line(frame, (x_max, y_max), (x_max - corner_len, y_max), (255, 0, 0), 3)
            cv2.line(frame, (x_max, y_max), (x_max, y_max - corner_len), (255, 0, 0), 3)

            # Gambar landmark tangan
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
            )

            # Titik WRIST sebagai pusat tangan
            wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
            cx_h = int(wrist.x * w_frame)
            cy_h = int(wrist.y * h_frame)

            cv2.circle(frame, (cx_h, cy_h), 8, (255, 255, 255), -1)

            # Hitung posisi tangan relatif terhadap tengah frame
            hand_position_text = get_position_label(cx_h, cy_h, w_frame, h_frame)

            print(f"Posisi tangan: {hand_position_text}")

        # Tampilkan teks posisi tangan
        cv2.putText(
            frame,
            f"Posisi tangan: {hand_position_text}",
            (30, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 0),
            2,
            cv2.LINE_AA,
        )

        # Tampilkan hasil
        cv2.imshow("Face + Hand Tracking - tekan 'q' untuk keluar", frame)

        # Tekan q untuk keluar
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Bersihkan
    cap.release()
    hands.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
