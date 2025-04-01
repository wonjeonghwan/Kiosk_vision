"""
데이터베이스 관련 기능
"""

import sqlite3
import os
import numpy as np
from typing import List, Tuple, Optional
from app.config import DB_PATH
from app.models.user import UserData

class Database:
    def __init__(self):
        """데이터베이스 초기화"""
        self.db_path = DB_PATH
        self.create_tables()
    
    def create_tables(self):
        """테이블 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 사용자 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                face_encoding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_menu_items(self, limit: Optional[int] = None) -> List[Tuple]:
        """메뉴 아이템 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            if limit:
                cursor.execute("SELECT item, price, image FROM menus LIMIT ?", (limit,))
            else:
                cursor.execute("SELECT item, price, image FROM menus")
            rows = cursor.fetchall()
            return rows
        except sqlite3.OperationalError:
            # 테이블 구조 확인
            cursor.execute("PRAGMA table_info(menus)")
            columns = cursor.fetchall()
            print("현재 테이블 구조:", columns)
            raise
        finally:
            conn.close()
    
    def get_menu_item_by_name(self, item_name: str) -> Optional[Tuple]:
        """메뉴 이름으로 상세 정보 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT item, price, image FROM menus WHERE item = ?",
            (item_name,)
        )
        row = cursor.fetchone()
        conn.close()
        return row if row else None
    
    def get_user_by_face_encoding(self, face_encoding: bytes) -> Optional[UserData]:
        """얼굴 인코딩으로 사용자 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE face_encoding = ?", (face_encoding,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return UserData.from_db_row(row)
        return None
    
    def add_user(self, name, face_encoding):
        """사용자 추가"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, face_encoding) VALUES (?, ?)",
            (name, face_encoding)
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    def get_user(self, user_id):
        """사용자 정보 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def get_all_users(self):
        """모든 사용자 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        conn.close()
        return users
    
    def get_user_by_name(self, name):
        """이름으로 사용자 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def update_user(self, user_id, name=None, face_encoding=None):
        """사용자 정보 업데이트"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if name and face_encoding:
            cursor.execute(
                "UPDATE users SET name = ?, face_encoding = ? WHERE id = ?",
                (name, face_encoding, user_id)
            )
        elif name:
            cursor.execute(
                "UPDATE users SET name = ? WHERE id = ?",
                (name, user_id)
            )
        elif face_encoding:
            cursor.execute(
                "UPDATE users SET face_encoding = ? WHERE id = ?",
                (face_encoding, user_id)
            )
        
        conn.commit()
        conn.close()
    
    def delete_user(self, user_id):
        """사용자 삭제"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close() 