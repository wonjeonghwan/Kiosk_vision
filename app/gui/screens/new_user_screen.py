"""
새로운 사용자 등록 화면
"""

import cv2
import numpy as np
import time
from PIL import Image as PILImage, ImageDraw, ImageFont
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import RoundedRectangle
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from app.config import BOLD_FONT_PATH, LIGHT_FONT_PATH, BACK_IMG, LOGO_IMG, CHARACTER_IMG
from app.gui.widgets.touch_keyboard import TouchKeyboard
from app.core.face_detection import track_target_face, MAX_LOST_FRAMES
from .base_screen import BaseScreen
from app.core.tts import TTSManager
import os
from kivy.uix.scrollview import ScrollView

class NewUserScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(NewUserScreen, self).__init__(**kwargs)
        
        # 다음 화면 설정
        self.next_screen = "order"
        
        # 메인 레이아웃
        self.layout = FloatLayout()
        self.camera = None
        self.lost_frame_count = 0
        self.last_tracking_time = time.time()
        
        # STT 초기화
        self.vad_loop = None
        self.is_listening = False
        
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
            text="신규 사용자 등록",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.045,
            color=(0, 0, 0, 1),
            pos_hint={'center_x': 0.5, 'top': 1.44},
            halign='center',
            valign='middle'
        )
        self.overlay.add_widget(self.title_label)
        
        # 레이아웃에 오버레이 추가
        self.layout.add_widget(self.overlay)
        
        # 이름 입력 필드
        self.name_input = Label(
            text='',
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.06,
            color=(0, 0, 0, 1),
            size_hint=(1, 0.1),
            pos_hint = {'center_x': 0.5, 'center_y': 0.23},
            halign='center',
            valign='middle'
        )
        self.layout.add_widget(self.name_input)
        
        # 터치 키보드
        self.keyboard = TouchKeyboard(self.on_keyboard_input)
        self.keyboard.size_hint = (0.9, 0.2)  # 키보드 크기 조정
        self.keyboard.pos_hint = {'center_x': 0.5, 'center_y': 0.1}  # 위치 조정
        self.layout.add_widget(self.keyboard)
        
        self.add_widget(self.layout)
    
    def on_enter(self):
        """화면 진입 시 호출"""
        super(NewUserScreen, self).on_enter()
        self.start_camera()
        # TTS로 안내 메시지 재생 후 STT 시작
        self.play_welcome_message()

    def on_leave(self):
        """화면 이탈 시 호출"""
        super(NewUserScreen, self).on_leave()
        self.stop_camera()
        # STT 종료
        self.stop_stt()

    def play_welcome_message(self):
        """TTS로 안내 메시지 재생"""
        try:
            # TTS 매니저 가져오기
            tts_manager = TTSManager()
            
            # 안내 메시지 재생
            # 올바른 경로로 수정
            welcome_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "audio", "gpt_sovits_v.wav")
            print(f"🔊 오디오 파일 경로: {welcome_path}")
            
            # 파일 존재 확인
            if os.path.exists(welcome_path):
                print(f"✅ 오디오 파일 존재: {welcome_path}")
                # 스크롤뷰 생성 및 설정
                scroll_view = ScrollView(
                    do_scroll_x=False,
                    do_scroll_y=False,
                    size_hint=(1, 1)
                )
                self.add_widget(scroll_view)
                
                # TTS 재생
                tts_manager.play_audio(welcome_path)
                
                # 3초 후에 스크롤뷰 제거 및 STT 시작
                Clock.schedule_once(lambda dt: self.remove_widget(scroll_view), 3)
                Clock.schedule_once(lambda dt: self.start_stt(), 3)
            else:
                print(f"❌ 오디오 파일 없음: {welcome_path}")
                # 파일이 없으면 바로 STT 시작
                self.start_stt()
        except Exception as e:
            print(f"❌ TTS 재생 중 오류: {str(e)}")
            # 오류 발생 시 바로 STT 시작
            self.start_stt()

    def start_stt(self):
        """STT 시작"""
        if not self.vad_loop:
            from app.core.vad_whisper_loop import VADWhisperLoop
            self.vad_loop = VADWhisperLoop(callback=self.handle_stt_input)
            self.vad_loop.start()
            self.is_listening = True
            # 안내 메시지 추가
            self.name_input.text = "이름을 말씀해주세요..."

    def stop_stt(self):
        """STT 종료"""
        if self.vad_loop:
            self.vad_loop.stop()
            self.vad_loop = None
        self.is_listening = False

    def handle_stt_input(self, text):
        """STT 입력 처리"""
        if self.is_listening:
            # 이름 입력 필드 업데이트
            self.name_input.text = text.strip()
            # 자동으로 확인 처리
            self.on_confirm(None)

    def on_keyboard_input(self, key):
        """키보드 입력 처리"""
        if key == 'backspace':
            self.name_input.text = self.name_input.text[:-1]
        elif key == 'enter':
            self.on_confirm(None)
        else:
            self.name_input.text += key
            # 키보드 입력 시 STT 중지
            if self.is_listening:
                self.stop_stt()
    
    def on_confirm(self, instance):
        """확인 버튼 클릭 시 호출"""
        name = self.name_input.text.strip()
        if not name:
            print("이름을 입력해주세요.")
            return
        
        # waiting 화면의 save_face 메서드 호출
        waiting_screen = self.manager.get_screen('waiting')
        if waiting_screen:
            waiting_screen.save_face(name)
            # order 화면으로 전환
            self.manager.current = 'order'
    
    def start_camera(self):
        if not self.camera:
            self.camera = cv2.VideoCapture(0)
            Clock.schedule_interval(self.update_camera, 1.0/30.0)
                
    def stop_camera(self):
        if self.camera:
            self.camera.release()
            self.camera = None
            Clock.unschedule(self.update_camera)
    
    def update_camera(self, dt):
        pass