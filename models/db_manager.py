import sqlite3
import numpy as np
import pickle
from models.config import DB_PATH

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
    """ ✅ 30프레임 동안 수집한 얼굴 벡터를 평균화하여 하나의 row로 저장 """
    # 30프레임 동안 수집한 벡터의 평균 계산 (128차원 평균 벡터 생성)
    mean_encoding = np.mean(encodings, axis=0)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 얼굴 정보 저장 (user_id, name, 평균 encoding)
    cursor.execute("INSERT INTO faces (name, encoding) VALUES (?, ?)",
                   (name, pickle.dumps(mean_encoding)))
    conn.commit()
    conn.close()

def find_best_match(encoding, threshold=0.45):
    """ 기존 사용자와 얼굴 매칭 """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, encoding FROM faces")
    rows = cursor.fetchall()
    conn.close()

    best_match_id = None
    best_match_name = None
    min_distance = threshold

    for row in rows:
        stored_encoding = pickle.loads(row[2])  # 바이너리 데이터를 Numpy 배열로 변환
        distance = np.linalg.norm(encoding - stored_encoding)

        if distance < min_distance:
            min_distance = distance
            best_match_id = row[0]
            best_match_name = row[1]

    return best_match_id, best_match_name
