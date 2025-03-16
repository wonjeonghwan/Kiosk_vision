# models/user_manager.py

import cv2
from models.db_manager import save_face, find_best_match
from models.config import SIMILARITY_THRESHOLD, REQUIRED_FRAMES

# 새로운 얼굴이 이미 등록된 사용자와 동일한지 확인
def check_new_user(encoding, track_id, stable_faces):
    """
    새로운 얼굴이 일정 프레임 이상 감지되면 신규 등록 여부 확인
    :param encoding: 감지된 얼굴의 특징 벡터 (128차원)
    :param stable_faces: 지속적으로 감지된 얼굴 정보 (딕셔너리)
    :return: 신규 등록 대상이면 True, 아니면 False
    """
    if track_id not in stable_faces:
        stable_faces[track_id] = 0
    stable_faces[track_id] += 1

    if stable_faces[track_id] >= REQUIRED_FRAMES:
        user_id, _ = find_best_match(encoding, SIMILARITY_THRESHOLD)
        return user_id is None  # DB에 없으면 신규 사용자
    return False

# 일정 시간 내 동일 얼굴이 여러 번 인식되는 문제 방지
def prevent_duplicate_registration(track_id, temporary_storage):
    """
    동일 얼굴이 반복적으로 신규 등록 요청을 받지 않도록 방지
    :param temporary_storage: 임시 저장소 (딕셔너리)
    :return: 이미 등록 요청된 경우 True, 아니면 False
    """
    if track_id in temporary_storage:
        return True
    temporary_storage[track_id] = True
    return False