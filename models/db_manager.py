import sqlite3
import numpy as np
import pickle
import uuid

DB_PATH = "faces.db"

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
    user_id = str(uuid.uuid4())  # ✅ 고유한 UUID 생성 (예: '550e8400-e29b-41d4-a716-446655440000')

    # 30프레임 동안 수집한 벡터의 평균 계산 (128차원 평균 벡터 생성)
    mean_encoding = np.mean(encodings, axis=0)
    conn = sqlite3.connect("faces.db")
    cursor = conn.cursor()

    # 얼굴 정보 저장 (user_id, name, 평균 encoding)
    cursor.execute("INSERT INTO faces (id, name, encoding) VALUES (?, ?, ?)",
                   (user_id, name, pickle.dumps(mean_encoding)))
    conn.commit()
    conn.close()

def find_best_match(encoding, threshold=0.45):
    """ 기존 사용자와 얼굴 매칭 """
    conn = sqlite3.connect(DB_PATH)     # DB 연결
    cursor = conn.cursor()              # 커서객체 생성(SQL 실행)
    cursor.execute("SELECT id, name, encoding FROM faces")  # SQL문 실행
    rows = cursor.fetchall()            # 가져온 모든 값을 rows에 저장
    conn.close()                        # DB 연결 닫기

    best_match_id = None        #빈 변수
    best_match_name = None      #빈 변수
    min_distance = threshold    #입력한 값(0.45)

    for row in rows:    # 모든 DB정보에 대한 for문
        stored_encoding = pickle.loads(row[2])  # 벡터화 한 데이터를 다시 numpy로 변환한 것을 변수에 넣고
        distance = np.linalg.norm(encoding - stored_encoding)   # 카메라로 받은 numpy값과 저장된 numpy의 차이를 변수에 넣고

        if distance < min_distance:     # 만약 해당 row가 입력값보다 차이가 적다면
            min_distance = distance     # 낮은 차이를 최소 값으로 지정 (가장 차이가 적은(맞는) 얼굴을 찾아감)
            best_match_id = row[0]      # id
            best_match_name = row[1]    # 이름(입력값)

    return best_match_id, best_match_name
