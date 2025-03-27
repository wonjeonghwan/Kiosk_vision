import sqlite3

DB_PATH = "Comfile_Coffee_DB.db"

def reset_users_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # users 테이블의 모든 데이터 삭제
    cursor.execute("DELETE FROM users;")
    
    conn.commit()
    conn.close()
    print("users 테이블 데이터 초기화 완료")

if __name__ == "__main__":
    reset_users_table()
