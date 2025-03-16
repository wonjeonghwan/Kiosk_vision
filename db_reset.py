import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect("faces.db")
cursor = conn.cursor()

# 기존 테이블 삭제 (모든 데이터 삭제됨)
cursor.execute("DROP TABLE IF EXISTS faces")

# 새 테이블 생성 (UUID 적용)
cursor.execute("""
    CREATE TABLE faces (
        id INTEGER PRIMARY KEY,  -- UUID를 기본 키로 사용
        name TEXT NOT NULL,
        encoding BLOB NOT NULL
    )
""")

conn.commit()
conn.close()

print("✅ faces.db 초기화 완료! (UUID 미적용)")