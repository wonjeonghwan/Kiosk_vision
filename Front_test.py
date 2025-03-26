import sys
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.texture import Texture
import cv2
import numpy as np
from face_detection import extract_face_embeddings, track_target_face, find_best_match, initialize_database
from PIL import Image as PILImage, ImageDraw, ImageFont
import sqlite3

# 윈도우 기본 한글 폰트 경로
SYSTEM_FONT_PATH = "C:/Windows/Fonts/malgun.ttf"

# 전역 변수: 주문번호 (발급페이지 노출 시마다 1씩 증가)
order_number = 0

# 인식된 사용자 이름
recognized_user_name = ""

# 전체 창 크기 설정
Window.size = (540, 960)

class WaitingScreen(Screen):
    """대기화면: 얼굴인식 시작 전 대기 화면"""
    def __init__(self, **kwargs):
        super(WaitingScreen, self).__init__(**kwargs)
        self.layout = FloatLayout()
        
        # 배경 이미지
        self.bg_image = Image(
            source='gunssak.jpeg',
            fit_mode='fill',
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.layout.add_widget(self.bg_image)
        
        # 카메라 화면을 표시할 이미지 위젯
        self.camera_image = Image(
            size_hint=(0.8, 0.4),
            pos_hint={'center_x': 0.5, 'center_y': 0.6}
        )
        self.layout.add_widget(self.camera_image)
        
        # 인식된 사용자 이름을 표시할 라벨
        self.user_label = Label(
            text="",
            font_name=SYSTEM_FONT_PATH,
            font_size=Window.height * 0.03,
            color=(255, 255, 255, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.3}
        )
        self.layout.add_widget(self.user_label)
        
        # 안내 라벨
        self.info_label = Label(
            text="얼굴 인식 진행 중...\n녹색 사각형 안에서 정면을 바라봐주세요",
            font_name=SYSTEM_FONT_PATH,
            font_size=Window.height * 0.03,
            color=(255, 255, 255, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.15}
        )
        self.layout.add_widget(self.info_label)
        self.add_widget(self.layout)
        
        # 카메라 관련 변수
        self.camera = None
        self.target_embedding = None
        self.current_encoding = None
        self.is_waiting_for_name = False

    def on_enter(self):
        """화면에 진입할 때"""
        # 두 이벤트 모두 바인딩합니다.
        Window.bind(on_key_down=self._on_keyboard_down)
        Window.bind(on_textinput=self._on_text_input)
        self.start_camera()
        initialize_database()

    def on_leave(self):
        """화면에서 나갈 때"""
        Window.unbind(on_keyboard_down=self._on_keyboard_down)
        self.stop_camera()

    def start_camera(self):
        """카메라 시작"""
        if not self.camera:
            self.camera = cv2.VideoCapture(0)
            Clock.schedule_interval(self.update_camera, 1.0/30.0)

    def stop_camera(self):
        """카메라 정지"""
        if self.camera:
            self.camera.release()
            self.camera = None
            Clock.unschedule(self.update_camera)

    def update_camera(self, dt):
        """카메라 프레임 업데이트"""
        if self.camera and not self.is_waiting_for_name:
            ret, frame = self.camera.read()
            if ret:
                # 얼굴 인식 처리
                encoding, (x1, y1, x2, y2), progress = extract_face_embeddings(frame)
                
                # 녹색 네모와 진행률 표시
                if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    # 한글 텍스트 표시를 위한 PIL 사용
                    frame_pil = PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    draw = ImageDraw.Draw(frame_pil)
                    font = ImageFont.truetype(SYSTEM_FONT_PATH, 30)
                    draw.text((10, 30), f"인식 진행률: {progress}%", font=font, fill=(0, 255, 0))
                    frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
                
                if encoding is not None and progress >= 100:
                    try:
                        # print("얼굴 인코딩 생성됨:", encoding.shape)  # 인코딩 형태 확인
                        self.target_embedding = encoding
                        self.current_encoding = encoding
                        # print("현재 인코딩 저장됨:", self.current_encoding.shape)  # 저장된 인코딩 확인
                        self.is_waiting_for_name = True
                        self.user_label.text = "새로운 사용자입니다\n이름을 입력하고 엔터를 눌러주세요"
                        Window.bind(on_textinput=self._on_text_input)
                    except Exception as e:
                        print(f"얼굴 인식 오류: {e}")
                        self.user_label.text = "얼굴 인식 중 오류가 발생했습니다"

                # OpenCV BGR을 RGB로 변환
                buf = cv2.flip(frame, 0).tobytes()
                texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.camera_image.texture = texture

    def _on_text_input(self, window, text):
        """이름 입력 처리 (on_textinput 이벤트 핸들러)"""
        if self.is_waiting_for_name:
            # Enter 입력 (줄바꿈 문자)이면 이름 완료 처리
            if text in ['\r', '\n']:
                name = self.user_label.text.split('\n')[2] if len(self.user_label.text.split('\n')) > 2 else ""
                if name:
                    print("이름 입력됨:", name)
                    from face_detection import save_face
                    save_face(name, self.current_encoding)
                    global recognized_user_name
                    recognized_user_name = name
                    self.is_waiting_for_name = False
                    Window.unbind(on_textinput=self._on_text_input)
                    self.manager.current = "menu"
            else:
                # 일반 문자 입력 (한글 포함)
                current_text = self.user_label.text.split('\n')
                if len(current_text) > 2:
                    current_text[2] = current_text[2] + text
                else:
                    current_text.append(text)
                self.user_label.text = '\n'.join(current_text)
        return True


    def _on_keyboard_down(self, window, key, scancode, codepoint, modifier):
        if self.is_waiting_for_name:
            if key == 8:  # Backspace
                current_text = self.user_label.text.split('\n')
                if len(current_text) > 2 and current_text[2]:
                    current_text[2] = current_text[2][:-1]
                    self.user_label.text = '\n'.join(current_text)
                return True
            elif key == 13:  # Enter 키 처리
                # 이름은 라벨의 3번째 줄에 저장되어 있다고 가정
                name = self.user_label.text.split('\n')[2] if len(self.user_label.text.split('\n')) > 2 else ""
                if name:
                    print("이름 입력됨:", name)
                    from face_detection import save_face
                    save_face(name, self.current_encoding)
                    global recognized_user_name
                    recognized_user_name = name
                    self.is_waiting_for_name = False
                    # 엔터 입력 후, on_textinput 이벤트 바인딩 해제
                    Window.unbind(on_textinput=self._on_text_input)
                    self.manager.current = "menu"
                return True
        # 이름 입력 모드가 아닐 때 일반 키 처리
        if key == ord('q'):
            self.stop_camera()
            App.get_running_app().stop()
            sys.exit(0)
        return True


class MenuDecisionScreen(Screen):
    """메뉴 결정 페이지"""
    def __init__(self, **kwargs):
        super(MenuDecisionScreen, self).__init__(**kwargs)
        self.layout = FloatLayout()
        self.label = Label(
            text="메뉴 결정 페이지\n(a 버튼을 눌러 진행)\n(s 버튼을 누르면 대기화면으로)",
            font_name=SYSTEM_FONT_PATH,
            font_size=Window.height * 0.03,
            color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.layout.add_widget(self.label)
        self.add_widget(self.layout)
        
        # 카메라 관련 변수
        self.camera = None
        self.last_check_time = 0

    def on_enter(self):
        global recognized_user_name
        self.label.text = f"메뉴 결정 페이지\n인식된 사용자: {recognized_user_name}\n(a 버튼을 눌러 진행)\n(s 버튼을 누르면 대기화면으로)"
        Window.bind(on_key_down=self._on_keyboard_down)  # 수정: on_textinput -> on_key_down
        self.start_camera()

    def on_leave(self):
        Window.unbind(on_key_down=self._on_keyboard_down)  # 수정: on_textinput -> on_key_down
        self.stop_camera()

    def start_camera(self):
        if not self.camera:
            self.camera = cv2.VideoCapture(0)
            Clock.schedule_interval(self.check_user_presence, 1.0)

    def stop_camera(self):
        if self.camera:
            self.camera.release()
            self.camera = None
            Clock.unschedule(self.check_user_presence)

    def check_user_presence(self, dt):
        if self.camera:
            ret, frame = self.camera.read()
            if ret:
                face_found = track_target_face(frame, self.manager.get_screen('waiting').target_embedding)
                if not face_found:
                    self.manager.current = "waiting"

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifier):
        if key == ord('a'):
            self.manager.current = "payment"
        elif key == ord('s'):
            self.manager.current = "waiting"
        elif key == ord('q'):
            self.stop_camera()
            App.get_running_app().stop()
            sys.exit(0)
        return True

class PaymentScreen(Screen):
    def __init__(self, **kwargs):
        super(PaymentScreen, self).__init__(**kwargs)
        self.camera = None  # 카메라 초기화 추가
        self.layout = FloatLayout()
        # 결제 라벨
        self.label = Label(
            text="결제",
            font_name=SYSTEM_FONT_PATH,
            font_size=Window.height * 0.03,
            color=(1, 0, 0, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        # 안내 라벨
        self.info = Label(
            text="(a 버튼을 눌러 진행,\n s 버튼을 누르면 대기화면으로)",
            font_name=SYSTEM_FONT_PATH,
            font_size=Window.height * 0.025,
            color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.2}
        )
        self.layout.add_widget(self.label)
        self.layout.add_widget(self.info)
        self.add_widget(self.layout)


    def on_enter(self):
        Window.bind(on_key_down=self._on_keyboard_down)  # 수정: on_textinput -> on_key_down
        self.start_camera()

    def on_leave(self):
        Window.unbind(on_key_down=self._on_keyboard_down)  # 수정: on_textinput -> on_key_down
        self.stop_camera()

    def start_camera(self):
        if not self.camera:
            self.camera = cv2.VideoCapture(0)
            Clock.schedule_interval(self.check_user_presence, 1.0)

    def stop_camera(self):
        if self.camera:
            self.camera.release()
            self.camera = None
            Clock.unschedule(self.check_user_presence)

    def check_user_presence(self, dt):
        if self.camera:
            ret, frame = self.camera.read()
            if ret:
                face_found = track_target_face(frame, self.manager.get_screen('waiting').target_embedding)
                if not face_found:
                    self.manager.current = "waiting"

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifier):
        if key == ord('a'):
            self.manager.current = "order"
        elif key == ord('s'):
            self.manager.current = "waiting"
        elif key == ord('q'):
            self.stop_camera()
            App.get_running_app().stop()
            sys.exit(0)
        return True

class OrderIssuanceScreen(Screen):
    def __init__(self, **kwargs):
        super(OrderIssuanceScreen, self).__init__(**kwargs)
        self.camera = None  # 카메라 초기화 추가
        self.layout = FloatLayout()
        # 주문번호 라벨
        self.order_label = Label(
            text="",
            font_name=SYSTEM_FONT_PATH,
            font_size=Window.height * 0.03,
            color=(0, 1, 0, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        # 안내 라벨
        self.info = Label(
            text="(a 버튼을 눌러 처음으로)",
            font_name=SYSTEM_FONT_PATH,
            font_size=Window.height * 0.025,
            color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.2}
        )
        self.layout.add_widget(self.order_label)
        self.layout.add_widget(self.info)
        self.add_widget(self.layout)


    def on_enter(self):
        global order_number
        order_number += 1
        self.order_label.text = f"주문번호: {order_number}"
        Window.bind(on_key_down=self._on_keyboard_down)  # 수정: on_textinput -> on_key_down
        self.start_camera()

    def on_leave(self):
        Window.unbind(on_key_down=self._on_keyboard_down)  # 수정: on_textinput -> on_key_down
        self.stop_camera()

    def start_camera(self):
        if not self.camera:
            self.camera = cv2.VideoCapture(0)
            Clock.schedule_interval(self.check_user_presence, 1.0)

    def stop_camera(self):
        if self.camera:
            self.camera.release()
            self.camera = None
            Clock.unschedule(self.check_user_presence)

    def check_user_presence(self, dt):
        if self.camera:
            ret, frame = self.camera.read()
            if ret:
                face_found = track_target_face(frame, self.manager.get_screen('waiting').target_embedding)
                if not face_found:
                    self.manager.current = "waiting"

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifier):
        if key == ord('a'):
            self.manager.current = "waiting"
        elif key == ord('q'):
            self.stop_camera()
            App.get_running_app().stop()
            sys.exit(0)
        return True

# -----------------------
# ScreenManager 설정
# -----------------------
class KioskScreenManager(ScreenManager):
    def __init__(self, **kwargs):
        super(KioskScreenManager, self).__init__(**kwargs)
        self.transition = FadeTransition()
        self.add_widget(WaitingScreen(name="waiting"))
        self.add_widget(MenuDecisionScreen(name="menu"))
        self.add_widget(PaymentScreen(name="payment"))
        self.add_widget(OrderIssuanceScreen(name="order"))

# -----------------------
# 전체 App 클래스
# -----------------------
class KioskApp(App):
    def build(self):
        return KioskScreenManager()

if __name__ == '__main__':
    KioskApp().run()