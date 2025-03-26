# main.py
import cv2
import numpy as np
import sqlite3
import pickle
import face_recognition
from deep_sort_realtime.deepsort_tracker import DeepSort
from PIL import ImageFont, ImageDraw, Image
import time

# 설정값
SIMILARITY_THRESHOLD = 0.45
REQUIRED_FRAMES = 15
DISAPPEAR_FRAMES = 90
MAX_LOST_FRAMES = 100
THRESHOLD = 0.85
TRACKER_MAX_AGE = 90
DELETE_TIMEOUT = 300
FONT_PATH = "malgun.ttf"
DB_PATH = "Comfile_Coffee_DB.db"
SYSTEM_FONT_PATH = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

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
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            face_encoding BLOB,
            name TEXT,
            phone TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
    """얼굴 정보 저장"""
    print("DB 저장 시작 - 이름:", name)
    print("인코딩 형태:", encodings.shape)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 인코딩을 BLOB 형태로 변환
    encoding_blob = pickle.dumps(encodings)
    print("변환된 인코딩 길이:", len(encoding_blob))
    
    # created_at은 자동으로 현재 시간이 입력됨
    c.execute('INSERT INTO users (face_encoding, name, phone) VALUES (?, ?, NULL)',
              (encoding_blob, name))
    conn.commit()
    conn.close()
    print("DB 저장 완료")

def find_best_match(encoding, threshold=THRESHOLD):
    """얼굴 매칭"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, name, face_encoding FROM users WHERE face_encoding IS NOT NULL")  # NULL이 아닌 데이터만 조회
    rows = cursor.fetchall()
    conn.close()

    best_match_id = None
    best_match_name = None
    best_similarity = 0

    for row in rows:
        if row[2] is not None:  # 추가 안전장치
            try:
                stored_encoding = pickle.loads(row[2])
                norm_product = np.linalg.norm(encoding) * np.linalg.norm(stored_encoding)
                if norm_product == 0:
                    continue
                similarity = np.dot(encoding, stored_encoding) / norm_product

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_id = row[0]
                    best_match_name = row[1]
            except Exception as e:
                print(f"얼굴 매칭 중 오류 발생: {e}")
                continue

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
            
            if face_stable_count >= REQUIRED_FRAMES:
                # 충분한 프레임이 모였을 때 매칭 시도
                mean_encoding = np.mean(temporary_encodings, axis=0)
                match = find_best_match(mean_encoding)
                
                if match[0] is not None:
                    # 기존 사용자 발견
                    print(f"ID:{match[0]},NAME:{match[1]}")
                    temporary_encodings.clear()
                    face_stable_count = 0
                    return mean_encoding, (x1, y1, x2, y2), 100
                else:
                    # 새로운 사용자 - DB에 저장
                    print("NEW_FACE - 저장 완료")
                    save_face("Unknown", mean_encoding)
                    temporary_encodings.clear()
                    face_stable_count = 0
                    return None, (x1, y1, x2, y2), 0
            
            return None, (x1, y1, x2, y2), int((face_stable_count / REQUIRED_FRAMES) * 100)
    
    face_stable_count = 0
    temporary_encodings.clear()
    return None, (x1, y1, x2, y2), 0

def track_target_face(frame, target_embedding):
    """얼굴 추적"""
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    
    face_found = False
    
    for (top, right, bottom, left), encoding in zip(face_locations, encodings):
        similarity = np.dot(encoding, target_embedding) / (np.linalg.norm(encoding) * np.linalg.norm(target_embedding))
        if similarity >= SIMILARITY_THRESHOLD:
            face_found = True
            break
    
    print(f"TRACKING:{face_found}")
    return face_found

def put_text(frame, text, position):
    """한글 텍스트를 이미지에 표시"""
    frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(frame_pil)
    font = ImageFont.truetype(SYSTEM_FONT_PATH, 30)
    draw.text(position, text, font=font, fill=(0, 255, 0))
    return cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)

def main():
    """메인 함수"""
    initialize_database()
    cap = cv2.VideoCapture(0)
    
    target_embedding = None
    tracking_enabled = False
    last_tracking_time = time.time()
    lost_frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if not tracking_enabled:
            # 얼굴 인식 모드
            encoding, (x1, y1, x2, y2), progress = extract_face_embeddings(frame)
            
            # 녹색 사각형 표시
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # 진행률 표시 (한글)
            frame = put_text(frame, f"인식 진행률: {progress}%", (10, 30))
            
            if encoding is not None and progress >= 100:
                target_embedding = encoding
                tracking_enabled = True
                last_tracking_time = time.time()
        else:
            # 얼굴 추적 모드
            current_time = time.time()
            if current_time - last_tracking_time >= 1.0:  # 1초마다 추적 상태 전송
                face_found = track_target_face(frame, target_embedding)
                if not face_found:
                    lost_frame_count += 1
                    if lost_frame_count > MAX_LOST_FRAMES:
                        tracking_enabled = False
                        target_embedding = None
                        lost_frame_count = 0
                else:
                    lost_frame_count = 0
                last_tracking_time = current_time
        
        cv2.imshow('Face Recognition', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()