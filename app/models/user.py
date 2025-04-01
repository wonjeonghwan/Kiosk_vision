"""
사용자 관련 데이터 모델
"""

from pydantic import BaseModel
from typing import Optional
import numpy as np

class UserData(BaseModel):
    user_id: Optional[int] = None
    name: str
    phone: str
    face_encoding: Optional[bytes] = None
    
    @classmethod
    def from_db_row(cls, row):
        """데이터베이스 행에서 UserData 객체 생성"""
        return cls(
            user_id=row[0],
            face_encoding=row[1],
            name=row[2],
            phone=row[3]
        )
    
    def get_face_encoding_array(self) -> Optional[np.ndarray]:
        """face_encoding 바이트를 numpy 배열로 변환"""
        if self.face_encoding:
            return np.frombuffer(self.face_encoding)
        return None 