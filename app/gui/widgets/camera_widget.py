"""
카메라 위젯
"""

import cv2
import numpy as np
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.clock import Clock
from kivy.core.window import Window
from app.config import CAMERA_WIDTH, CAMERA_HEIGHT
from app.core.face_detection import (
    check_face_quality,
    save_face,
    find_best_match,
    track_target_face,
    extract_face_embeddings
)

class CameraWidget(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 카메라 초기화
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        
        # 프레임 업데이트 이벤트
        self.update_event = Clock.schedule_interval(self.update, 1.0/30.0)
        
        # 얼굴 추적 상태
        self.tracking = False
        self.target_face = None
        self.target_face_embeddings = None
        
        # 콜백 함수
        self.on_face_detected = None
        self.on_face_lost = None
        self.on_face_quality_checked = None
        
    def update(self, dt):
        ret, frame = self.capture.read()
        if not ret:
            return
            
        # 프레임 처리
        if self.tracking and self.target_face_embeddings is not None:
            # 얼굴 추적
            face = track_target_face(frame, self.target_face_embeddings)
            if face is not None:
                self.target_face = face
                if self.on_face_detected:
                    self.on_face_detected(face)
            else:
                self.target_face = None
                if self.on_face_lost:
                    self.on_face_lost()
        else:
            # 얼굴 검출
            face = check_face_quality(frame)
            if face is not None:
                self.target_face = face
                self.target_face_embeddings = extract_face_embeddings(face)
                if self.on_face_detected:
                    self.on_face_detected(face)
                if self.on_face_quality_checked:
                    self.on_face_quality_checked(face)
        
        # 프레임 표시
        buf = cv2.flip(frame, 0).tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.texture = texture
        
    def start_tracking(self, face_embeddings):
        """얼굴 추적 시작"""
        self.tracking = True
        self.target_face_embeddings = face_embeddings
        
    def stop_tracking(self):
        """얼굴 추적 중지"""
        self.tracking = False
        self.target_face_embeddings = None
        
    def get_current_face(self):
        """현재 감지된 얼굴 반환"""
        return self.target_face
        
    def on_leave(self):
        """위젯이 제거될 때 정리"""
        self.update_event.cancel()
        self.capture.release() 