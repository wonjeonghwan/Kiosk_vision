import sqlite3
import numpy as np
import pickle
from models.config import DB_PATH, THRESHOLD

def initialize_database():
    """ 데이터베이스 초기화 (테이블 생성) """
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

def save_face(name, encodings):
    """ ✅ 얼굴 벡터 저장 개선 버전 """
    # 1. 이상치 제거
    distances = []
    mean_encoding = np.mean(encodings, axis=0)
    
    for enc in encodings:
        dist = np.linalg.norm(enc - mean_encoding)
        distances.append(dist)
    
    # 상위 80% 품질의 프레임만 선택
    threshold = np.percentile(distances, 80)
    good_encodings = [enc for enc, dist in zip(encodings, distances) if dist < threshold]
    
    # 2. 선별된 프레임으로 최종 평균 계산
    final_encoding = np.mean(good_encodings, axis=0)
    
    # 3. 저장
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO faces (name, encoding) VALUES (?, ?)",
                   (name, pickle.dumps(final_encoding)))
    conn.commit()
    conn.close()

def compare_face_features(encoding1, encoding2):
    """얼굴 특징점들 간의 구조적 차이 비교"""
    # 특징점들 간의 상대적 거리 비교
    feature_distances = []
    for i in range(0, len(encoding1), 2):
        dist1 = np.linalg.norm(encoding1[i:i+2])
        dist2 = np.linalg.norm(encoding2[i:i+2])
        feature_distances.append(abs(dist1 - dist2))
    
    # 특징점 거리 차이가 큰 경우 유사도 감소
    feature_diff = np.mean(feature_distances)
    return 1.0 / (1.0 + feature_diff)

def find_best_match(encoding, threshold=THRESHOLD):
    """ 개선된 얼굴 매칭 함수 """
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
        
        # 1. 코사인 유사도
        norm_product = np.linalg.norm(encoding) * np.linalg.norm(stored_encoding)
        if norm_product == 0:
            continue
        cosine_sim = np.dot(encoding, stored_encoding) / norm_product
        
        # 2. 유클리드 거리 기반 유사도
        euclidean_dist = np.linalg.norm(encoding - stored_encoding)
        euclidean_sim = 1 / (1 + euclidean_dist)
        
        # 3. 얼굴 특징점 구조 유사도
        feature_sim = compare_face_features(encoding, stored_encoding)
        
        # 4. 종합 유사도 (가중치 적용)
        similarity = 0.5 * cosine_sim + 0.3 * euclidean_sim + 0.2 * feature_sim

        if similarity > best_similarity:
            best_similarity = similarity
            best_match_id = row[0]
            best_match_name = row[1]

    if best_similarity >= threshold:
        return best_match_id, best_match_name, best_similarity
    else:
        return None, None, best_similarity
