"""
기본 화면 클래스
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from app.config import BOLD_FONT_PATH, LIGHT_FONT_PATH, BACK_IMG
import cv2
import time
from app.core.face_detection import track_target_face, MAX_LOST_FRAMES

class BaseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        
        # 카메라 관련 변수
        self.camera = None
        self.lost_frame_count = 0
        self.last_tracking_time = time.time()
        
        # 배경 이미지 설정
        self.background = Image(
            source=BACK_IMG,
            allow_stretch=True,
            keep_ratio=False
        )
        self.layout.add_widget(self.background)
        
        # 폰트 등록
        LabelBase.register('Bold', BOLD_FONT_PATH)
        LabelBase.register('Light', LIGHT_FONT_PATH)
        
        # 컨텐츠 레이아웃
        self.content = AnchorLayout()
        self.layout.add_widget(self.content)
        
        self.add_widget(self.layout)
    
    def start_camera(self):
        """카메라 시작"""
        if self.camera is None:
            self.camera = cv2.VideoCapture(0)
            Clock.schedule_interval(self.update_camera, 1.0/30.0)  # 30 FPS
    
    def stop_camera(self):
        """카메라 중지"""
        if self.camera is not None:
            Clock.unschedule(self.update_camera)
            self.camera.release()
            self.camera = None
    
    def update_camera(self, dt):
        pass
    
    def check_face_tracking(self, frame):
        """얼굴 추적 확인"""
        try:
            current_time = time.time()
            if current_time - self.last_tracking_time >= 3.0:  # 3초마다 추적 상태 확인
                face_found = track_target_face(frame, self.manager.get_screen('waiting').target_embedding)
                if not face_found:
                    self.lost_frame_count += 1
                    print(f"이탈 카운트: {self.lost_frame_count}")
                    if self.lost_frame_count >= MAX_LOST_FRAMES:
                        print("대기화면으로 전환")
                        self.manager.current = "waiting"
                else:
                    self.lost_frame_count = 0
                self.last_tracking_time = current_time
        except Exception as e:
            print(f"얼굴 추적 중 오류 발생: {e}")
    
    def add_content(self, widget):
        """컨텐츠 위젯 추가"""
        self.content.add_widget(widget)
    
    def clear_content(self):
        """컨텐츠 위젯 제거"""
        self.content.clear_widgets()
    
    def show_message(self, text: str, duration: float = 2.0):
        """메시지 표시"""
        message = Label(
            text=text,
            font_name='Bold',
            size_hint=(None, None),
            size=(400, 50)
        )
        self.add_content(message)
        
        def remove_message(dt):
            self.content.remove_widget(message)
        
        Clock.schedule_once(remove_message, duration)
