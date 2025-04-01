"""
주문번호 발급 화면
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.app import App
from kivy.clock import Clock
import sys
import cv2
import numpy as np
from app.config import BOLD_FONT_PATH, BACK_IMG, LOGO_IMG, CHARACTER_IMG
from app.gui.widgets import RoundedButton
from .base_screen import BaseScreen
from app.core.face_detection import track_target_face, MAX_LOST_FRAMES
import time

# 전역 주문번호 변수
order_number = 0

class OrderIssuanceScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(OrderIssuanceScreen, self).__init__(**kwargs)
        
        # 다음 화면 설정
        self.next_screen = "waiting"
        
        # 메인 레이아웃
        self.layout = FloatLayout()
        
        # 배경 이미지
        self.bg_image = Image(
            source=BACK_IMG,
            fit_mode='fill',
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.layout.add_widget(self.bg_image)
        
        # 로고 이미지
        self.logo_image = Image(
            source=LOGO_IMG,
            size_hint=(0.45, 0.1),
            pos_hint={'center_x': 0.5, 'top': 0.88}
        )
        self.layout.add_widget(self.logo_image)
        
        # 캐릭터 이미지
        self.character_image = Image(
            source=CHARACTER_IMG,
            size_hint=(1.4, 1.4),
            pos_hint={'center_x': 0.5, 'center_y': 0.35}
        )
        self.layout.add_widget(self.character_image)
        
        # 반투명 오버레이
        self.overlay = FloatLayout(
            size_hint=(0.95, 0.33),
            pos_hint={'center_x': 0.5, 'bottom': 0}
        )
        
        # 오버레이 모서리 둥글게
        def update_rect(*args):
            self.overlay.canvas.before.clear()
            with self.overlay.canvas.before:
                Color(0.94, 0.94, 0.94, 0.5)
                RoundedRectangle(
                    pos=self.overlay.pos,
                    size=self.overlay.size,
                    radius=[(20, 20), (20, 20), (0, 0), (0, 0)]
                )
        self.overlay.bind(size=update_rect, pos=update_rect)
        
        # 페이지 타이틀
        self.title_label = Label(
            text="주문 완료",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.03,
            color=(0, 0, 0, 1),
            pos_hint={'center_x': 0.5, 'top': 1.44},
            halign='center',
            valign='middle'
        )
        self.overlay.add_widget(self.title_label)
        
        # 주문 번호 표시
        self.order_label = Label(
            text="",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.09,
            color=(0, 0, 0, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.6},
            halign='center',
            valign='middle'
        )
        self.overlay.add_widget(self.order_label)
        
        # 레이아웃에 오버레이 추가
        self.layout.add_widget(self.overlay)
        
        # 메인 레이아웃을 화면에 추가
        self.add_widget(self.layout)
        
        # 주문 번호
        self.order_number = 0

    def on_enter(self):
        """화면 진입 시 호출"""
        self.start_camera()
        # 주문 번호 증가
        self.order_number += 1
        self.order_label.text = f"주문번호: {self.order_number}"

    def on_leave(self):
        """화면 이탈 시 호출"""
        self.stop_camera()

    def start_camera(self):
        """카메라 시작"""
        try:
            if self.camera is None:
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    return
                
                # 카메라 해상도 설정 (4:3 비율)
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
                # 카메라 프레임 업데이트 스케줄러 시작 (1초 간격)
                Clock.schedule_interval(self.update_camera, 1.0)  # 1 FPS
        except Exception:
            pass

    def stop_camera(self):
        """카메라 중지"""
        try:
            if self.camera is not None:
                # 카메라 프레임 업데이트 스케줄러 중지
                Clock.unschedule(self.update_camera)
                # 카메라 해제
                self.camera.release()
                self.camera = None
        except Exception:
            pass

    def update_camera(self, dt):
        """카메라 프레임 업데이트"""
        if self.camera is None:
            return
            
        ret, frame = self.camera.read()
        if not ret:
            return
            
        try:
            # 얼굴 추적 확인
            self.check_face_tracking(frame)
        except Exception:
            pass

    def check_face_tracking(self, frame):
        """얼굴 추적 확인"""
        try:
            current_time = time.time()
            if current_time - self.last_tracking_time >= 3.0:
                # waiting 화면의 target_embedding 확인
                waiting_screen = self.manager.get_screen('waiting')
                if waiting_screen and hasattr(waiting_screen, 'target_embedding') and waiting_screen.target_embedding is not None:
                    face_found = track_target_face(frame, waiting_screen.target_embedding)
                    if not face_found:
                        self.lost_frame_count += 1
                        if self.lost_frame_count >= MAX_LOST_FRAMES:
                            self.manager.current = "waiting"
                    else:
                        self.lost_frame_count = 0
                self.last_tracking_time = current_time
        except Exception:
            pass

    def on_touch_down(self, touch):
        """터치 이벤트 처리"""
        # 화면 전환
        self.manager.current = "waiting"
        return True 