# main.py
import torch
import cv2
import numpy as np
from ultralytics import YOLO
from models.deepsort_tracker import track_target_face
from models.face_recognizer import extract_face_embeddings, temporary_encodings
from models.db_manager import save_face, find_best_match
from PIL import ImageFont, ImageDraw, Image
from models.config import MAX_LOST_FRAMES, THRESHOLD

# ✅ GPU 설정
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

FONT_PATH = "malgun.ttf"
model = YOLO("models/yolov8n.pt").to(device)
cap = cv2.VideoCapture(0)

target_embedding = None
tracking_enabled = False
user_name = ""
lost_frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    if not tracking_enabled:
        encoding, (x1, y1, x2, y2), progress = extract_face_embeddings(frame)

        if encoding is not None:
            user_id, name, similarity = find_best_match(encoding, threshold=THRESHOLD)

            if user_id and similarity >= THRESHOLD:
                print(f"✅ 기존 사용자 인식됨: {name} (유사도 {similarity:.2f})")
                target_embedding = encoding
                user_name = name
                tracking_enabled = True

            elif progress >= 100:
                print("🆕 이름을 입력하세요. (취소: 'C')")
                new_user_name = input("이름 입력: ").strip()
                if new_user_name.lower() == "c":
                    print("❌ 등록 취소됨")
                elif new_user_name:
                    save_face(new_user_name, temporary_encodings)
                    print(f"✅ '{new_user_name}' 저장 완료!")
                    target_embedding = encoding
                    user_name = new_user_name
                    tracking_enabled = True

        # 인식 중 박스 표시
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    else:
        # 추적만 수행
        frame, face_found = track_target_face(frame, target_embedding, name=user_name)

        if not face_found:
            lost_frame_count += 1
        else:
            lost_frame_count = 0

        if lost_frame_count > MAX_LOST_FRAMES:
            print("⚠️ 얼굴 놓침. 인식 모드로 복귀")
            tracking_enabled = False
            target_embedding = None
            user_name = ""
            lost_frame_count = 0

    # UI
    frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(frame_pil)
    font = ImageFont.truetype(FONT_PATH, 30)

    if tracking_enabled and user_name:
        draw.text((50, 50), f"✅ {user_name}", font=font, fill=(255, 255, 0, 255))
    elif not tracking_enabled and progress > 0:
        draw.text((50, 50), f"인식 진행: {progress}%", font=font, fill=(0, 255, 0, 255))

    frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
    cv2.imshow("Face Recognition & Tracking", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
