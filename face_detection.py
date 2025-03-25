# main.py
import cv2
import numpy as np
import sqlite3
import pickle
import face_recognition
from deep_sort_realtime.deepsort_tracker import DeepSort
from PIL import ImageFont, ImageDraw, Image
from ultralytics import YOLO

# 설정값
SIMILARITY_THRESHOLD = 0.45
REQUIRED_FRAMES = 30
DISAPPEAR_FRAMES = 90
MAX_LOST_FRAMES = 100
THRESHOLD = 0.85
TRACKER_MAX_AGE = 90
DELETE_TIMEOUT = 300
FONT_PATH = "malgun.ttf"
DB_PATH = "faces.db"

# 전역 변수
face_stable_count = 0
temporary_encodings = []

# DeepSORT 초기화
tracker = DeepSort(
    max_age=15,
    embedder="mobilenet",
    half=True
)

def initialize_database():
    """데이터베이스 초기화"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            encoding BLOB
        )
    """)
    conn.commit()
    conn.close()

def check_face_quality(face_img):
    """얼굴 이미지의 품질을 검사"""
    laplacian_var = cv2.Laplacian(face_img, cv2.CV_64F).var()
    if laplacian_var < 100:
        return False
        
    brightness = np.mean(face_img)
    if brightness < 40 or brightness > 250:
        return False
        
    contrast = np.std(face_img)
    if contrast < 20:
        return False
        
    return True

def save_face(name, encodings):
    """얼굴 벡터 저장"""
    distances = []
    mean_encoding = np.mean(encodings, axis=0)
    
    for enc in encodings:
        dist = np.linalg.norm(enc - mean_encoding)
        distances.append(dist)
    
    threshold = np.percentile(distances, 80)
    good_encodings = [enc for enc, dist in zip(encodings, distances) if dist < threshold]
    final_encoding = np.mean(good_encodings, axis=0)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO faces (name, encoding) VALUES (?, ?)",
                   (name, pickle.dumps(final_encoding)))
    conn.commit()
    conn.close()

def find_best_match(encoding, threshold=THRESHOLD):
    """얼굴 매칭"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, encoding FROM faces")
    rows = cursor.fetchall()
    conn.close()

    best_match_id = None
    best_match_name = None
    best_similarity = 0

    for row in rows:
        stored_encoding = pickle.loads(row[2])
        norm_product = np.linalg.norm(encoding) * np.linalg.norm(stored_encoding)
        if norm_product == 0:
            continue
        similarity = np.dot(encoding, stored_encoding) / norm_product

        if similarity > best_similarity:
            best_similarity = similarity
            best_match_id = row[0]
            best_match_name = row[1]

    if best_similarity >= threshold:
        return best_match_id, best_match_name, best_similarity
    return None, None, best_similarity

def extract_face_embeddings(frame):
    """얼굴 특징 추출"""
    global face_stable_count, temporary_encodings

    h, w, _ = frame.shape
    x1, y1, x2, y2 = w//3, h//4, 2*w//3, 3*h//4
    face_crop = frame[y1:y2, x1:x2]

    if face_crop is None or face_crop.size == 0:
        face_stable_count = 0
        temporary_encodings.clear()
        return None, (x1, y1, x2, y2), 0

    rgb_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_face)
    encodings = face_recognition.face_encodings(rgb_face, face_locations)

    if encodings:
        max_area = 0
        best_encoding = None
        
        for (top, right, bottom, left), encoding in zip(face_locations, encodings):
            area = (bottom - top) * (right - left)
            if area > max_area:
                face_img = rgb_face[top:bottom, left:right]
                if check_face_quality(face_img):
                    max_area = area
                    best_encoding = encoding
        
        if best_encoding is not None:
            face_stable_count = min(REQUIRED_FRAMES, face_stable_count + 1)
            temporary_encodings.append(best_encoding)
            return best_encoding, (x1, y1, x2, y2), int((face_stable_count / REQUIRED_FRAMES) * 100)

    face_stable_count = 0
    temporary_encodings.clear()
    return None, (x1, y1, x2, y2), 0

def track_target_face(frame, target_embedding, similarity_threshold=0.8, name=""):
    """얼굴 추적"""
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    candidates = []
    for (top, right, bottom, left), encoding in zip(face_locations, encodings):
        similarity = np.dot(encoding, target_embedding) / (np.linalg.norm(encoding) * np.linalg.norm(target_embedding))
        if similarity >= similarity_threshold:
            x, y, w, h = left, top, right - left, bottom - top
            candidates.append({
                "box": [x, y, w, h],
                "similarity": similarity
            })

    detections = []
    face_found = False

    if candidates:
        candidates.sort(key=lambda c: c["similarity"], reverse=True)
        best = candidates[0]
        detections.append((best["box"], 0.99, 'target'))
        face_found = True

    tracks = tracker.update_tracks(detections, frame=frame)

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

def main():
    """메인 함수"""
    initialize_database()
    model = YOLO("models/yolov8n.pt")
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

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        else:
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
                face_stable_count = 0
                temporary_encodings.clear()

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

if __name__ == "__main__":
    main()