import sqlite3
import pickle
import numpy as np
import face_recognition
import cv2
import os
from datetime import datetime

# 데이터베이스 경로
DB_PATH = "Comfile_Coffee_DB.db"

def initialize_database():
    """데이터베이스 초기화"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 기존 테이블 삭제
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS menus")
    cursor.execute("DROP TABLE IF EXISTS orders")
    
    # 테이블 새로 생성
    cursor.execute("""
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            face_encoding BLOB NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE menus (
            menu_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            image_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            menu_id INTEGER,
            quantity INTEGER NOT NULL,
            total_price INTEGER NOT NULL,
            order_status TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (menu_id) REFERENCES menus(menu_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("데이터베이스 초기화 완료")

if __name__ == "__main__":
    initialize_database()