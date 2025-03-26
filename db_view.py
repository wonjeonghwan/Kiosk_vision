import sqlite3
import pandas as pd

# 데이터베이스 연결
conn = sqlite3.connect("Comfile_Coffee_DB.db")
cursor = conn.cursor()

# 테이블 목록 확인
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"📌 존재하는 테이블: {tables}")

# faces 테이블 데이터 조회
df = pd.read_sql_query("SELECT * FROM users", conn)
conn.close()

print("📌 데이터베이스 내용:")
print(df)

# 확인 = python db_test.py