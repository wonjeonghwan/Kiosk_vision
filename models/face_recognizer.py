import face_recognition
import cv2
import numpy as np
from models.config import REQUIRED_FRAMES

face_stable_count = 0
temporary_encodings = []

def check_face_quality(face_img):
    """얼굴 이미지의 품질을 검사합니다."""
    # 블러 검사
    laplacian_var = cv2.Laplacian(face_img, cv2.CV_64F).var()
    if laplacian_var < 100:  # 블러 임계값
        return False
        
    # 밝기 검사
    brightness = np.mean(face_img)
    if brightness < 40 or brightness > 250:  # 너무 어두우거나 밝은 경우
        return False
        
    # 대비 검사
    contrast = np.std(face_img)
    if contrast < 20:  # 대비가 너무 낮은 경우
        return False
        
    return True

def reset_recognition_state():
    """인식 상태 초기화"""
    global face_stable_count, temporary_encodings
    face_stable_count = 0
    temporary_encodings.clear()

def extract_face_embeddings(frame):
    global face_stable_count, temporary_encodings

    # 고정된 영역 설정
    h, w, _ = frame.shape
    x1, y1, x2, y2 = w//3, h//4, 2*w//3, 3*h//4
    face_crop = frame[y1:y2, x1:x2]

    # 얼굴이 없거나 인식 실패 시 완전 초기화
    if face_crop is None or face_crop.size == 0:
        face_stable_count = 0
        temporary_encodings.clear()
        return None, (x1, y1, x2, y2), 0

    rgb_face = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_face)
    encodings = face_recognition.face_encodings(rgb_face, face_locations)

    if encodings:
        # 가장 큰 얼굴 찾기
        max_area = 0
        best_encoding = None
        
        for (top, right, bottom, left), encoding in zip(face_locations, encodings):
            area = (bottom - top) * (right - left)
            if area > max_area:
                face_img = rgb_face[top:bottom, left:right]
                if check_face_quality(face_img):
                    max_area = area
                    best_encoding = encoding
        
        if best_encoding is not None:
            face_stable_count = min(REQUIRED_FRAMES, face_stable_count + 1)
            temporary_encodings.append(best_encoding)
            # 항상 고정된 영역 반환
            return best_encoding, (x1, y1, x2, y2), int((face_stable_count / REQUIRED_FRAMES) * 100)

    # 얼굴 인식 실패 시 완전 초기화
    face_stable_count = 0
    temporary_encodings.clear()
    return None, (x1, y1, x2, y2), 0
