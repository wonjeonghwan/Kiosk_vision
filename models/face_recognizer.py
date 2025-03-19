import face_recognition
import cv2
import numpy as np
from models.config import REQUIRED_FRAMES

# 얼굴 감지 상태 저장 (새로운 사용자 확인을 위한 변수)
face_stable_count = 0  # 30프레임 이상 유지될 때만 새로운 사용자로 판단
temporary_encodings = []  # ✅ 새로운 사용자의 다양한 얼굴을 저장하는 리스트

def extract_face_embeddings(frame):
    """ 중앙 네모 박스 내 얼굴을 감지하고, 지속 시간(%) 반환 """
    global face_stable_count, temporary_encodings

    h, w, _ = frame.shape
    x1, y1, x2, y2 = w//3, h//4, 2*w//3, 3*h//4  # 중앙 부분 네모 영역
    face_crop = frame[y1:y2, x1:x2]

    if face_crop is None or face_crop.size == 0:
        face_stable_count = max(0, face_stable_count - 1)  # 얼굴이 없으면 안정 시간 감소
        temporary_encodings.clear()  # 얼굴이 사라지면 임시 저장 데이터 삭제
        return None, (x1, y1, x2, y2), 0  # 진행도 0%

    rgb_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
    encodings = face_recognition.face_encodings(rgb_face)
 
    if encodings:
        face_stable_count = min(REQUIRED_FRAMES, face_stable_count + 1)  # 얼굴이 감지되면 카운트 증가
        temporary_encodings.append(encodings[0])  # ✅ 새로운 사용자일 경우 다양한 얼굴 저장
    else:
        face_stable_count = max(0, face_stable_count - 1)  # 얼굴이 없으면 안정 시간 감소
        temporary_encodings.clear()  # 얼굴이 사라지면 임시 저장 데이터 삭제

    progress = int((face_stable_count / REQUIRED_FRAMES) * 100)  # 0~100% 진행률 계산
    return encodings[0] if encodings else None, (x1, y1, x2, y2), progress

# # 전체 화면에서 얼굴 감지 - 얼굴에서 특징 벡터(128차원) 추출
# def extract_face_embeddings(frame, bbox):
#     x1, y1, x2, y2 = bbox

#     # 얼굴 영역 크롭
#     face_crop = frame[y1:y2, x1:x2]
#     if face_crop is None or face_crop.size == 0:
#         return None  

#     # BGR → RGB 변환 (face_recognition 라이브러리는 RGB를 사용)
#     rgb_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)

#     # 얼굴 특징 벡터(128차원) 추출
#     encodings = face_recognition.face_encodings(rgb_face)

#     return encodings[0] if encodings else None
