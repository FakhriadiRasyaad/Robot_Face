import cv2
import mediapipe as mp

def get_position_label(cx, cy, width, height):
    """
    Menentukan posisi tangan relatif terhadap tengah frame.
    Hasil hanya salah satu dari: 'KIRI', 'KANAN', 'ATAS', 'BAWAH'
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

    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils

    # Hanya 1 tangan
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Gagal membaca frame dari kamera")
            break

        # Balikkan frame biar mirip mirror (opsional)
        frame = cv2.flip(frame, 1)

        h, w, _ = frame.shape

        # MediaPipe pakai RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)

        posisi_teks = "Tidak ada tangan"

        if results.multi_hand_landmarks:
            # Ambil hanya tangan pertama (karena max_num_hands=1)
            hand_landmarks = results.multi_hand_landmarks[0]

            # Contoh: pakai titik pergelangan tangan (WRIST) sebagai pusat
            wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
            cx = int(wrist.x * w)
            cy = int(wrist.y * h)

            # Hitung posisi (kiri/kanan/atas/bawah)
            posisi_teks = get_position_label(cx, cy, w, h)

            # Gambar landmark tangan
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
            )

            # Gambar titik pusat (WRIST)
            cv2.circle(frame, (cx, cy), 8, (255, 255, 255), -1)

        # Tampilkan teks posisi di bagian atas
        cv2.putText(
            frame,
            f"Posisi: {posisi_teks}",
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

        cv2.imshow("Deteksi Posisi Tangan", frame)

        # Tekan 'q' untuk keluar
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    hands.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
