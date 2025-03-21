import torch
import cv2
import numpy as np
import face_recognition
from deep_sort_realtime.deepsort_tracker import DeepSort
from PIL import ImageFont, ImageDraw, Image
from models.config import FONT_PATH

# ✅ GPU 설정
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

tracker = DeepSort(
    max_age=15,
    embedder="mobilenet",  # 가벼운 모델 사용
    half=True,  # FP16 연산으로 속도 개선
    embedder_gpu=(device.type == "cuda")  # ✅ GPU 사용 설정
)

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def track_target_face(frame, target_embedding, similarity_threshold=0.8, name=""):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    candidates = []
    for (top, right, bottom, left), encoding in zip(face_locations, encodings):
        similarity = cosine_similarity(encoding, target_embedding)
        if similarity >= similarity_threshold:
            x, y, w, h = left, top, right - left, bottom - top
            candidates.append({
                "box": [x, y, w, h],
                "similarity": similarity
            })

    detections = []
    face_found = False

    if candidates:
        # 유사도 기준 가장 유사한 것만 추적
        candidates.sort(key=lambda c: c["similarity"], reverse=True)
        best = candidates[0]
        detections.append((best["box"], 0.99, 'target'))
        face_found = True

    # DeepSORT 추적
    tracks = tracker.update_tracks(detections, frame=frame)

    # PIL 텍스트 표시
    frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(frame_pil)
    font = ImageFont.truetype(FONT_PATH, 30)

    for track in tracks:
        if not track.is_confirmed():
            continue
        l, t, r, b = track.to_ltrb()
        cv2.rectangle(frame, (int(l), int(t)), (int(r), int(b)), (0, 255, 255), 2)
        if name:
            draw.text((int(l), int(t) - 35), f"{name}", font=font, fill=(0, 255, 255, 255))

    frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
    return frame, face_found
