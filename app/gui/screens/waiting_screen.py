"""
대기 화면
"""

import cv2
import numpy as np
import time
from PIL import Image as PILImage, ImageDraw, ImageFont
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from app.config import BOLD_FONT_PATH, LIGHT_FONT_PATH, BACK_IMG, LOGO_IMG, CHARACTER_IMG
from app.core.face_detection import extract_face_embeddings, track_target_face, find_best_match, initialize_database, MAX_LOST_FRAMES, save_face
from .base_screen import BaseScreen
from app.service.api_client import register_user
from app.core.tts import TTSManager

# 설정값
SIMILARITY_THRESHOLD = 0.45
CAMERA_SCALE = 1.5  # 카메라 화면 크기 확대 비율

class WaitingScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(WaitingScreen, self).__init__(**kwargs)
        
        # 다음 화면 설정
        self.next_screen = "new_user"
        
        # 메인 레이아웃
        self.layout = FloatLayout()
        self.camera = None
        self.lost_frame_count = 0
        self.last_tracking_time = time.time()
        
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
        
        
        # 레이아웃에 오버레이 추가
        self.layout.add_widget(self.overlay)
        
        # 카메라 이미지
        self.camera_image = Image(
            size_hint=(0.45, 0.45),
            pos_hint={'center_x': 0.5, 'center_y': 0.14}
        )
        self.layout.add_widget(self.camera_image)
        
        # 안내 텍스트
        self.label = Label(
            text="녹색 사각형 안에서 정면을 바라보세요",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.05,
            color=(255, 255, 255, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.28},
            halign='center',
            valign='middle'
        )
        self.layout.add_widget(self.label)
        # TTS 초기화
        self.tts = TTSManager()
        self.tts.play_async("녹색 사각형 안에서 정면을 바라보세요")
        
        self.target_embedding = None
        self.current_encoding = None
        
        self.add_widget(self.layout)
    
    def on_enter(self):
        """화면 진입 시 호출"""
        initialize_database()
        self.start_camera()
    
    def on_leave(self):
        """화면 이탈 시 호출"""
        self.stop_camera()
    
    def start_camera(self):
        """카메라 시작"""
        self.camera = cv2.VideoCapture(0)
        # 카메라 해상도 설정 (4:3 비율)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        Clock.schedule_interval(self.update_camera, 1.0/30.0)
    
    def stop_camera(self):
        """카메라 중지"""
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        Clock.unschedule(self.update_camera)
    
    def update_camera(self, dt):
        """카메라 프레임 업데이트"""
        if self.camera is None:
            return
            
        ret, frame = self.camera.read()
        if not ret:
            print("카메라 프레임 읽기 실패")
            return
            
        try:
            # 얼굴 검출
            face_encoding, face_location, progress, match_result = extract_face_embeddings(frame)
            
            # 얼굴이 검출된 경우
            if face_encoding is not None:
                self.current_encoding = face_encoding
                
                # 매칭 결과가 있는 경우
                if match_result is not None and match_result[0] is not None:
                    print(f"기존 사용자 발견: ID:{match_result[0]}, NAME:{match_result[1]}")
                    self.target_embedding = face_encoding
                    self.manager.current = "order"
                elif progress >= 100:
                    print("신규 사용자 발견")
                    self.target_embedding = face_encoding
                    self.manager.current = "new_user"
            else:
                self.lost_frame_count += 1
                if self.lost_frame_count >= MAX_LOST_FRAMES:
                    print("얼굴 인식 실패 - 대기화면으로 전환")
                    self.manager.current = "waiting"
                else:
                    self.lost_frame_count = 0
            
            # 프레임 표시
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.flip(frame, 1)  # 좌우 반전
            
            # 프레임 크기 조정 (4:3 비율 유지)
            target_width = int(Window.width * 0.8)
            target_height = int(target_width * 3/4)  # 4:3 비율
            frame = cv2.resize(frame, (target_width, target_height))
            
            # 중앙에 고정된 크기의 녹색 사각형 그리기
            rect_width = int(target_width * 0.3)  # 화면 너비의 30%
            rect_height = int(target_height * 0.6)  # 화면 높이의 60%
            rect_x1 = (target_width - rect_width) // 2
            rect_y1 = (target_height - rect_height) // 2
            rect_x2 = rect_x1 + rect_width
            rect_y2 = rect_y1 + rect_height
            cv2.rectangle(frame, (rect_x1, rect_y1), (rect_x2, rect_y2), (0, 255, 0), 2)
            
            # 진행률 표시
            frame_pil = PILImage.fromarray(frame)
            draw = ImageDraw.Draw(frame_pil)
            font = ImageFont.truetype(BOLD_FONT_PATH, 30)
            draw.text((10, 30), f"인식 진행률: {progress}%", font=font, fill=(0, 255, 0))
            frame = np.array(frame_pil)
            
            # OpenCV 프레임을 Kivy 텍스처로 변환
            buf = cv2.flip(frame, 0).tostring()
            texture = self.camera_image.texture
            texture = self.camera_image.texture = Texture.create(size=frame.shape[1::-1], colorfmt='rgb')
            texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
            
        except Exception as e:
            print(f"카메라 프레임 처리 중 오류 발생: {e}")
            import traceback
            print(traceback.format_exc())
    
    def save_face(self, name):
        """얼굴 정보 저장"""
        if self.current_encoding is not None:
            # 얼굴 정보를 프론트 데이터베이스에 저장
            save_face(name, self.current_encoding)
            # 서버 신규 사용자 등록 
            dummy_number = "010-0000-0000"
            register_user(name,dummy_number,self.current_encoding)
            # waiting 화면으로 돌아가기
            self.manager.current = 'waiting'
        else:
            print("얼굴 인코딩이 없습니다.") 