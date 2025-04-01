import sys
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import cv2
import numpy as np
from face_detection import extract_face_embeddings, track_target_face, find_best_match, initialize_database, MAX_LOST_FRAMES
from PIL import Image as PILImage, ImageDraw, ImageFont
import sqlite3
import time

# 윈도우 기본 한글 폰트 경로
BOLD_FONT_PATH = "Source/NotoSansKR-Bold.ttf"
LIGHT_FONT_PATH = "Source/NotoSansKR-Light.ttf"
BACK_IMG = "Source/BG_pattern.png"

# 전역 변수: 주문번호 (발급페이지 노출 시마다 1씩 증가)
order_number = 0

# 인식된 사용자 이름
recognized_user_name = ""

# 전체 창 크기 설정
Window.size = (540, 960)

class OrderData:
    def __init__(self, cart_items):
        self.cart_items = cart_items
        self.total_price = sum(item["price"] * item["count"] for item in cart_items)
    
    @staticmethod
    def get_dummy_order_data():
        try:
            conn = sqlite3.connect("Comfile_Coffee_DB.db")
            cursor = conn.cursor()
            cursor.execute("SELECT item, price, image FROM menus LIMIT 3")
            rows = cursor.fetchall()
            conn.close()
            order_data = []
            for row in rows:
                order_data.append({"item": row[0], "price": row[1], "image": row[2], "count": 1})
            return order_data
        except Exception as e:
            print("DB에서 dummy order data 로드 실패:", e)
            return [
                {"item": "Americano", "price": 4000, "image": "Source/americano.png", "count": 1},
                {"item": "Latte", "price": 4500, "image": "Source/latte.png", "count": 2},
                {"item": "Espresso", "price": 3500, "image": "Source/espresso.png", "count": 1}
            ]

# ----- 둥근 모서리 버튼 클래스 -----
class RoundedButton(Button):
    def __init__(self, **kwargs):
        super(RoundedButton, self).__init__(**kwargs)
        # (2) 버튼 글씨: 검은색, BOLD 폰트
        self.font_name = BOLD_FONT_PATH
        self.color = (0, 0, 0, 1)  # 글자색 검은색
        self.background_normal = ''
        self.background_color = (252/255.0, 208/255.0, 41/255.0, 0.85)
        
        with self.canvas.before:
            Color(*self.background_color)
            # (1) 모서리를 [(20, 20), (20, 20), (0, 0), (0, 0)]로 변경
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[(20), (20), (20), (20)]
            )
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


# ----- 얇은 구분선 위젯 (가로길이 50%, 가운데 정렬) -----
class DividerLine(BoxLayout):
    def __init__(self, **kwargs):
        super(DividerLine, self).__init__(**kwargs)
        self.size_hint = (0.5, None)   # 가로길이 50%
        self.height = 1               # 얇은 선 두께
        self.pos_hint = {'center_x': 0.5}  # 가운데 정렬
        with self.canvas:
            Color(0, 0, 0, 0.5)  # 검은색
            self.rect = Rectangle(pos=self.pos, size=(0, 0))
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = (self.width, self.height)

# ----- 기본 화면 클래스 (공통 기능 구현) -----
class BaseScreen(Screen):
    def __init__(self, **kwargs):
        super(BaseScreen, self).__init__(**kwargs)
        self.layout = FloatLayout()
        self.camera = None
        
        # 얼굴 추적 관련 변수 추가
        self.lost_frame_count = 0
        self.last_tracking_time = time.time()
        
        # 배경 이미지 (가장 아래)
        self.bg_image = Image(
            source=BACK_IMG,
            fit_mode='fill',
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        self.layout.add_widget(self.bg_image)

        # 로고 이미지
        self.logo_image = Image(
            source="Source/compose_logo.png",
            size_hint=(0.45, 0.1),
            pos_hint={'center_x': 0.5, 'top': 0.88}
        )
        self.layout.add_widget(self.logo_image)

        # 캐릭터 이미지
        self.character_image = Image(
            source="Source/V_sample.png",
            size_hint=(1.4, 1.4),
            pos_hint={'center_x': 0.5, 'center_y': 0.35}
        )
        self.layout.add_widget(self.character_image)

        # 반투명 오버레이 창 (가장 위)
        self.overlay = FloatLayout(
            size_hint=(0.95, 0.33),
            pos_hint={'center_x': 0.5, 'bottom': 0}
        )
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
        self.layout.add_widget(self.overlay)
        self.add_widget(self.layout)

    def check_face_tracking(self, frame):
        try:
            current_time = time.time()
            if current_time - self.last_tracking_time >= 3.0:
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

# 대기화면: 얼굴인식 시작 전 화면
class WaitingScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(WaitingScreen, self).__init__(**kwargs)
        
        self.camera_image = Image(
            size_hint=(0.6, 0.2),
            pos_hint={'center_x': 0.5, 'center_y': 0.125}
        )
        self.layout.add_widget(self.camera_image)
        
        self.user_label = Label(
            text="",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.03,
            color=(255, 255, 255, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
            halign='center',
            valign='middle'
        )
        self.layout.add_widget(self.user_label)
        
        self.info_label_bold = Label(
            text="얼굴 인식 진행 중...",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.032,
            color=(255, 255, 255, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.3},
            halign='center',
            valign='middle'
        )
        self.layout.add_widget(self.info_label_bold)
        
        self.info_label_light = Label(
            text="녹색 사각형 안에서 정면을 바라봐주세요",
            font_name=LIGHT_FONT_PATH,
            font_size=Window.height * 0.015,
            color=(255, 255, 255, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.265},
            halign='center',
            valign='middle'
        )
        self.layout.add_widget(self.info_label_light)
        
        self.target_embedding = None
        self.current_encoding = None
        self.is_waiting_for_name = False

    def on_enter(self):
        Window.bind(on_key_down=self._on_keyboard_down)
        Window.bind(on_textinput=self._on_text_input)
        self.start_camera()
        initialize_database()

    def on_leave(self):
        Window.unbind(on_key_down=self._on_keyboard_down)
        self.stop_camera()

    def update_camera(self, dt):
        if self.camera and not self.is_waiting_for_name:
            ret, frame = self.camera.read()
            if ret:
                encoding, (x1, y1, x2, y2), progress, match_result = extract_face_embeddings(frame)
                if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    frame_pil = PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    draw = ImageDraw.Draw(frame_pil)
                    font = ImageFont.truetype(BOLD_FONT_PATH, 30)
                    draw.text((10, 30), f"인식 진행률: {progress}%", font=font, fill=(0, 252, 0))
                    frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
                if encoding is not None and progress >= 100:
                    if match_result is not None and match_result[0] is not None:
                        global recognized_user_name
                        recognized_user_name = match_result[1]
                        self.target_embedding = encoding
                        self.current_encoding = encoding
                        self.manager.current = "menu"
                    else:
                        self.target_embedding = encoding
                        self.current_encoding = encoding
                        self.manager.current = "newuser"
                buf = cv2.flip(frame, 0).tobytes()
                texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.camera_image.texture = texture

    def _on_text_input(self, window, text):
        if self.is_waiting_for_name:
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
                current_text = self.user_label.text.split('\n')
                if len(current_text) > 2:
                    current_text[2] = current_text[2] + text
                else:
                    current_text.append(text)
                self.user_label.text = '\n'.join(current_text)
        return True

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifier):
        if self.is_waiting_for_name:
            if key == 8:
                current_text = self.user_label.text.split('\n')
                if len(current_text) > 2 and current_text[2]:
                    current_text[2] = current_text[2][:-1]
                    self.user_label.text = '\n'.join(current_text)
                return True
            elif key == 13:
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
                return True
        if key == ord('q'):
            self.stop_camera()
            App.get_running_app().stop()
            sys.exit(0)
        return True

# ----- 터치 키보드 위젯 -----
class TouchKeyboard(BoxLayout):
    def __init__(self, callback, **kwargs):
        super(TouchKeyboard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 0  # 행 간격을 0으로 설정
        self.padding = 1  # 패딩 유지
        self.callback = callback
        
        # 초성, 중성, 종성 상태 변수 추가
        self.cho = ''  # 초성
        self.jung = ''  # 중성
        self.jong = ''  # 종성
        self.shift_mode = False  # shift 모드 상태
        
        # 일반 키와 shift 키 매핑
        self.key_mapping = {
            'ㄱ': 'ㄲ', 'ㄷ': 'ㄸ', 'ㅂ': 'ㅃ', 'ㅅ': 'ㅆ', 'ㅈ': 'ㅉ',
            'ㅐ': 'ㅒ', 'ㅔ': 'ㅖ'
        }
        
        # 키보드 레이아웃 정의 (shift 버튼 추가)
        self.normal_keys = [
            ['ㅂ', 'ㅈ', 'ㄷ', 'ㄱ', 'ㅅ', 'ㅛ', 'ㅕ', 'ㅑ', 'ㅐ', 'ㅔ'],
            ['ㅁ', 'ㄴ', 'ㅇ', 'ㄹ', 'ㅎ', 'ㅗ', 'ㅓ', 'ㅏ', 'ㅣ'],
            ['ㅋ', 'ㅌ', 'ㅊ', 'ㅍ', 'ㅠ', 'ㅜ', 'ㅡ']
        ]
        
        self.shift_keys = [
            ['ㅃ', 'ㅉ', 'ㄸ', 'ㄲ', 'ㅆ', 'ㅛ', 'ㅕ', 'ㅑ', 'ㅒ', 'ㅖ'],
            ['ㅁ', 'ㄴ', 'ㅇ', 'ㄹ', 'ㅎ', 'ㅗ', 'ㅓ', 'ㅏ', 'ㅣ'],
            ['ㅋ', 'ㅌ', 'ㅊ', 'ㅍ', 'ㅠ', 'ㅜ', 'ㅡ']
        ]
        
        # 키보드 생성
        self.key_buttons = []  # 버튼 참조 저장용
        
        # 자음/모음 키 행 생성
        for row_keys in self.normal_keys:
            row_layout = BoxLayout(spacing=1)  # 간격 줄임
            row_buttons = []
            for key in row_keys:
                btn = RoundedButton(
                    text=key,
                    size_hint=(0.08, 0.8),
                    font_size=16,
                    font_name=BOLD_FONT_PATH
                )
                btn.bind(on_release=lambda x, k=key: self.on_key_press(k))
                row_layout.add_widget(btn)
                row_buttons.append(btn)
            self.key_buttons.append(row_buttons)
            self.add_widget(row_layout)
        
        # 특수 키 행 생성
        special_row = BoxLayout(spacing=1)  # 간격 줄임
        
        shift_btn = RoundedButton(
            text='shift',
            size_hint=(0.15, 0.8),
            font_size=16,
            font_name=BOLD_FONT_PATH,
            background_color=(200/255.0, 200/255.0, 200/255.0, 0.85)
        )
        shift_btn.bind(on_release=lambda x: self.toggle_shift_mode())
        special_row.add_widget(shift_btn)
        
        space_btn = RoundedButton(
            text='스페이스',
            size_hint=(0.3, 0.8),
            font_size=16,
            font_name=BOLD_FONT_PATH
        )
        space_btn.bind(on_release=lambda x: self.on_key_press('스페이스'))
        special_row.add_widget(space_btn)
        
        backspace_btn = RoundedButton(
            text='←',
            size_hint=(0.15, 0.8),
            font_size=16,
            font_name=BOLD_FONT_PATH
        )
        backspace_btn.bind(on_release=lambda x: self.on_key_press('백스페이스'))
        special_row.add_widget(backspace_btn)
        
        enter_btn = RoundedButton(
            text='엔터',
            size_hint=(0.15, 0.8),
            font_size=16,
            font_name=BOLD_FONT_PATH
        )
        enter_btn.bind(on_release=lambda x: self.on_key_press('엔터'))
        special_row.add_widget(enter_btn)
        
        self.add_widget(special_row)
        self.shift_btn = shift_btn

    def toggle_shift_mode(self):
        self.shift_mode = not self.shift_mode
        # shift 버튼 배경색 변경
        self.shift_btn.background_color = (252/255.0, 208/255.0, 41/255.0, 0.85) if self.shift_mode else (200/255.0, 200/255.0, 200/255.0, 0.85)
        
        # 버튼 텍스트 변경
        for row_idx, row_buttons in enumerate(self.key_buttons):
            for btn_idx, btn in enumerate(row_buttons):
                btn.text = self.shift_keys[row_idx][btn_idx] if self.shift_mode else self.normal_keys[row_idx][btn_idx]

    def on_key_press(self, key):
        # shift 모드에서 키가 눌렸을 때 해당하는 쌍자음/쌍모음으로 변환
        if self.shift_mode and key in self.key_mapping:
            key = self.key_mapping[key]
            self.shift_mode = False  # 자동으로 shift 모드 해제
            self.toggle_shift_mode()  # 버튼 텍스트 원래대로 복원
            
        if key == '스페이스':
            # 현재 조합 중인 글자가 있다면 먼저 완성
            if self.cho or self.jung or self.jong:
                combined = self.combine_jamo()
                if combined:
                    self.callback(combined)
                self.cho = self.jung = self.jong = ''
            self.callback(' ')
            
        elif key == '백스페이스':
            # 현재 조합 중인 글자가 있다면 마지막 자모음만 삭제
            if self.jong:
                self.jong = ''
                combined = self.combine_jamo()
                if combined:
                    self.callback('backspace')
                    self.callback(combined)
            elif self.jung:
                self.jung = ''
                if self.cho:  # 초성만 남은 경우
                    self.callback('backspace')
                    self.callback(self.cho)
            elif self.cho:
                self.cho = ''
                self.callback('backspace')
            else:
                self.callback('backspace')
                
        elif key == '엔터':
            # 현재 조합 중인 글자가 있다면 먼저 완성
            if self.cho or self.jung or self.jong:
                combined = self.combine_jamo()
                if combined:
                    self.callback(combined)
                self.cho = self.jung = self.jong = ''
            self.callback('enter')
            
        else:
            # 자모음 분류
            CONSONANTS = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
            VOWELS = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
            
            if key in CONSONANTS:
                if not self.cho:  # 초성이 없으면 초성으로
                    self.cho = key
                    self.callback(key)
                elif not self.jung:  # 중성이 없는데 자음이 들어오면 이전 글자 완성하고 새로 시작
                    self.callback('backspace')
                    self.cho = key
                    self.callback(key)
                elif not self.jong:  # 종성이 없으면 종성으로
                    self.jong = key
                    combined = self.combine_jamo()
                    if combined:
                        self.callback('backspace')
                        self.callback(combined)
                else:  # 모든 자리가 찼으면 이전 글자 완성하고 새로 시작
                    combined = self.combine_jamo()
                    if combined:
                        self.callback('backspace')
                        self.callback(combined)
                    self.cho = key
                    self.jung = self.jong = ''
                    self.callback(key)
                    
            elif key in VOWELS:
                if not self.cho:  # 초성이 없는 모음
                    self.callback(key)
                elif not self.jung:  # 중성이 없으면 중성으로
                    self.jung = key
                    combined = self.combine_jamo()
                    if combined:
                        self.callback('backspace')
                        self.callback(combined)
                else:  # 중성이 있으면 이전 글자 완성하고 새로 시작
                    combined = self.combine_jamo()
                    if combined:
                        self.callback('backspace')
                        self.callback(combined)
                    self.cho = ''
                    self.jung = key
                    self.jong = ''
                    self.callback(key)

    def combine_jamo(self):
        if not self.cho or not self.jung:  # 초성과 중성이 모두 있어야 조합 가능
            return None
            
        CHO = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        JUNG = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
        JONG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']

        try:
            cho_idx = CHO.index(self.cho)
            jung_idx = JUNG.index(self.jung)
            jong_idx = JONG.index(self.jong) if self.jong else 0

            # 유니코드 조합
            unicode_value = 0xAC00 + cho_idx * 21 * 28 + jung_idx * 28 + jong_idx
            return chr(unicode_value)
        except ValueError:
            return None

# 신규 사용자 등록 화면
class NewUserScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(NewUserScreen, self).__init__(**kwargs)
        
        # 이름 입력 라벨
        self.user_label = Label(
            text="안녕? 처음 왔구나\n넌 이름이 뭐야?",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.03,
            color=(255, 255, 255, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.3},
            halign='center',
            valign='middle'
        )
        self.layout.add_widget(self.user_label)
        
        # 입력된 이름 표시 라벨
        self.name_label = Label(
            text="",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.04,
            color=(255, 255, 255, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.25},
            halign='center',
            valign='middle'
        )
        self.layout.add_widget(self.name_label)
        
        # 터치 키보드 추가 (크기 조정)
        self.keyboard = TouchKeyboard(
            callback=self.on_keyboard_input,
            size_hint=(0.8, 0.25),  # 크기를 80% 너비, 25% 높이로 조정
            pos_hint={'center_x': 0.5, 'bottom': 0.05}
        )
        self.layout.add_widget(self.keyboard)
        
        self.current_encoding = None

    def on_keyboard_input(self, key):
        if key == 'backspace':
            self.name_label.text = self.name_label.text[:-1]
        elif key == 'enter':
            name = self.name_label.text
            if name:
                print("이름 입력됨:", name)
                from face_detection import save_face
                save_face(name, self.current_encoding)
                global recognized_user_name
                recognized_user_name = name
                self.manager.current = "menu"
        elif key == '스페이스':
            self.name_label.text += ' '
        else:
            self.name_label.text += key

    def on_enter(self):
        Window.bind(on_key_down=self._on_keyboard_down)
        Window.bind(on_textinput=self._on_text_input)
        self.current_encoding = self.manager.get_screen('waiting').current_encoding

    def on_leave(self):
        Window.unbind(on_key_down=self._on_keyboard_down)
        Window.unbind(on_textinput=self._on_text_input)

    def _on_text_input(self, window, text):
        if text in ['\r', '\n']:
            name = self.name_label.text
            if name:
                print("이름 입력됨:", name)
                from face_detection import save_face
                save_face(name, self.current_encoding)
                global recognized_user_name
                recognized_user_name = name
                self.manager.current = "menu"
        else:
            self.name_label.text += text
        return True

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifier):
        if key == 8:  # 백스페이스
            self.name_label.text = self.name_label.text[:-1]
        elif key == 13:  # 엔터
            name = self.name_label.text
            if name:
                print("이름 입력됨:", name)
                from face_detection import save_face
                save_face(name, self.current_encoding)
                global recognized_user_name
                recognized_user_name = name
                self.manager.current = "menu"
        elif key == ord('q'):
            App.get_running_app().stop()
            sys.exit(0)
        return True

# 메뉴 결정 페이지 (메뉴 선택)
class MenuDecisionScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(MenuDecisionScreen, self).__init__(**kwargs)
        self.label = Label(
            text="",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.03,
            color=(255, 255, 255, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.2},
            halign='center',
            valign='middle'
        )
        self.layout.add_widget(self.label)
        self.last_check_time = 0

    def on_enter(self):
        global recognized_user_name
        self.label.text = f"메뉴 결정 페이지\n인식된 사용자: {recognized_user_name}\n(a 버튼을 눌러 장바구니로)\n(s 버튼을 누르면 대기화면으로)"
        Window.bind(on_key_down=self._on_keyboard_down)
        self.start_camera()

    def on_leave(self):
        Window.unbind(on_key_down=self._on_keyboard_down)
        self.stop_camera()

    def update_camera(self, dt):
        if self.camera:
            ret, frame = self.camera.read()
            if ret:
                self.check_face_tracking(frame)

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifier):
        if key == ord('a'):
            # 메뉴 선택 후 결제 전 장바구니로 이동
            self.manager.current = "cart"
        elif key == ord('s'):
            self.manager.current = "waiting"
        elif key == ord('q'):
            self.stop_camera()
            App.get_running_app().stop()
            sys.exit(0)
        return True

    def on_touch_down(self, touch):
        self.manager.current = "cart"
        return True

# ----- 장바구니 페이지 -----
class CartScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(CartScreen, self).__init__(**kwargs)

        # (A) 오버레이 모서리 둥글게 변경
        def update_rect(*args):
            self.overlay.canvas.before.clear()
            with self.overlay.canvas.before:
                Color(0.94, 0.94, 0.94, 0.5)
                # 오버레이도 네 모서리를 둥글게
                RoundedRectangle(
                    pos=self.overlay.pos,
                    size=self.overlay.size,
                    radius=[20, 20, 20, 20]
                )
        self.overlay.bind(size=update_rect, pos=update_rect)

        # 페이지 타이틀
        self.title_label = Label(
            text="주문 확인",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.03,
            color=(0, 0, 0, 1),
            pos_hint={'center_x': 0.5, 'top': 1.44},
            halign='center',
            valign='middle'
        )
        self.overlay.add_widget(self.title_label)
        
        # 스크롤뷰 (동일)
        self.cart_scroll = ScrollView(
            size_hint=(0.9, 0.58),
            pos_hint={'center_x': 0.5, 'center_y': 0.6},
            scroll_type=['bars','content'],
            bar_width=10,
            bar_color=(252/255.0, 208/255.0, 41/255.0, 0.85),
            bar_inactive_color=(252/255.0, 208/255.0, 41/255.0, 0.5)
        )
        self.cart_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=10)
        self.cart_box.bind(minimum_height=self.cart_box.setter('height'))
        self.cart_scroll.add_widget(self.cart_box)
        self.overlay.add_widget(self.cart_scroll)
        
        # (B) 하단 바를 BoxLayout으로 설정: 버튼 & 총 금액 한 줄 배치
        #     pos_hint로 y값을 올려서 조금 더 위로 배치
        self.bottom_bar = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.15),
            pos_hint={'x': 0, 'y': 0.08},  # y값을 0.08 정도로 하여 위로 이동
            spacing=10,
            padding=[10, 5]
        )

        self.add_button = RoundedButton(
            text="메뉴 추가",
            font_size=18,
            size_hint=(0.3, 0.8)
        )
        self.pay_button = RoundedButton(
            text="결제하기",
            font_size=18,
            size_hint=(0.3, 0.8)
        )
        self.total_label = Label(
            text="총 금액: 0원",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.023,
            color=(0, 0, 0, 1),
            halign='center',
            valign='middle',
            size_hint=(0.4, 1)
        )

        # (메뉴 추가 | 결제하기 | 총 금액) 순서로 배치
        self.bottom_bar.add_widget(self.add_button)
        self.bottom_bar.add_widget(self.pay_button)
        self.bottom_bar.add_widget(self.total_label)
        
        self.overlay.add_widget(self.bottom_bar)
        
        # 장바구니 데이터 로드
        self.cart_items = self.load_dummy_cart_data()
        
        # 버튼 이벤트
        self.add_button.bind(on_release=self.go_to_menu_decision)
        self.pay_button.bind(on_release=self.proceed_to_payment)

        self.refresh_cart_view()

    def load_dummy_cart_data(self):
        items = []
        try:
            conn = sqlite3.connect("Comfile_Coffee_DB.db")
            cursor = conn.cursor()
            cursor.execute("SELECT item, price, image FROM menus LIMIT 3")
            rows = cursor.fetchall()
            conn.close()
            for row in rows:
                items.append({"item": row[0], "price": row[1], "image": row[2], "count": 1})
        except Exception as e:
            print("DB에서 dummy cart data 로드 실패:", e)
            items = [
                {"item": "아이스 아메리카노", "price": 5000, "image": "data/menu_images_png/menu_image21.png", "count": 1},
                {"item": "아이스 라떼", "price": 5500, "image": "data/menu_images_png/menu_image24.png", "count": 1},
                {"item": "생딸기주스", "price": 4300, "image": "data/menu_images_png/menu_image17.png", "count": 1}
            ]
        return items

    def refresh_cart_view(self):
        self.cart_box.clear_widgets()
        for idx, item in enumerate(self.cart_items):
            widget = CartItemWidget(
                cart_item=item,
                index=idx,
                update_callback=self.update_cart_item,
                delete_callback=self.delete_cart_item
            )
            self.cart_box.add_widget(widget)
            
            # 위젯 사이에 구분선 추가 (마지막 아이템 제외)
            if idx < len(self.cart_items) - 1:
                divider = DividerLine()
                self.cart_box.add_widget(divider)
        
        # 총 금액 계산
        total = sum(i["price"] * i["count"] for i in self.cart_items)
        self.total_label.text = f"총 금액: {total}원"

    def update_cart_item(self, index, new_count):
        if 0 <= index < len(self.cart_items):
            self.cart_items[index]["count"] = new_count
            self.refresh_cart_view()

    def delete_cart_item(self, index):
        if 0 <= index < len(self.cart_items):
            del self.cart_items[index]
            self.refresh_cart_view()

    def go_to_menu_decision(self, instance):
        self.manager.current = "menu"

    def proceed_to_payment(self, instance):
        self.manager.current = "payment"

    def clear_cart(self):
        self.cart_items = []
        self.refresh_cart_view()

    def on_enter(self):
        self.start_camera()

    def on_leave(self):
        self.stop_camera()

    def update_camera(self, dt):
        if self.camera:
            ret, frame = self.camera.read()
            if ret:
                self.check_face_tracking(frame)

# ----- 장바구니 항목 위젯 (이미지, 이름, 갯수, 버튼들, 가격 순서) -----
class CartItemWidget(BoxLayout):
    def __init__(self, cart_item, index, update_callback, delete_callback, **kwargs):
        super(CartItemWidget, self).__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 90
        self.index = index
        self.cart_item = cart_item
        self.update_callback = update_callback
        self.delete_callback = delete_callback
        
        # 이미지
        # 이미지: AnchorLayout 컨테이너를 사용하여 셀 크기는 유지하고, 이미지 크기와 위치를 미세 조정
        self.image_container = AnchorLayout(
            size_hint=(0.15, 1),
            anchor_x='center',   # 원하는 정렬('left', 'center', 'right' 등)
            anchor_y='center',   # 원하는 정렬('bottom', 'center', 'top' 등)
            padding=(10, 5, 10, 5)  # (left, top, right, bottom) 순서로 여백 조절
        )
        self.image = Image(
            source=cart_item["image"],
            size_hint=(None, None),
            size=(145, 145),       # 원하는 이미지 크기로 조정
            allow_stretch=True,
            keep_ratio=True
        )
        self.image_container.add_widget(self.image)
        self.add_widget(self.image_container)

        
        # 상품명
        self.item_label = Label(
            text=cart_item["item"],
            font_name=BOLD_FONT_PATH,
            font_size=20,
            halign='left',
            valign='middle',
            color=(0,0,0,1),
            size_hint=(0.2, 1)
        )
        self.add_widget(self.item_label)
        
        # 갯수
        self.count_label = Label(
            text=f"{cart_item['count']}개",
            font_name=LIGHT_FONT_PATH,
            font_size=20,
            halign='center',
            valign='middle',
            color=(0,0,0,1),
            size_hint=(0.15, 1)
        )
        self.add_widget(self.count_label)
        
        # 버튼 레이아웃
        btn_layout = BoxLayout(
            orientation="vertical",
            size_hint=(0.08, 1),
            spacing=2,
            padding=(2, 2)
        )
        self.plus_btn = RoundedButton(
            text="+",
            font_name=BOLD_FONT_PATH,
            font_size=25,
            size_hint=(1, 0.3)
        )
        self.minus_btn = RoundedButton(
            text="-",
            font_name=BOLD_FONT_PATH,
            font_size=25,
            size_hint=(1, 0.3)
        )
        self.delete_btn = RoundedButton(
            text="삭제",
            font_name=BOLD_FONT_PATH,
            font_size=18,
            size_hint=(1, 0.3)
        )
        self.plus_btn.bind(on_release=self.increase_count)
        self.minus_btn.bind(on_release=self.decrease_count)
        self.delete_btn.bind(on_release=self.delete_item)
        btn_layout.add_widget(self.plus_btn)
        btn_layout.add_widget(self.minus_btn)
        btn_layout.add_widget(self.delete_btn)
        self.add_widget(btn_layout)
        
        # 가격
        self.price_label = Label(
            text=f"{cart_item['price']}원",
            font_name=LIGHT_FONT_PATH,
            font_size=20,
            halign='right',
            valign='middle',
            color=(0,0,0,1),
            size_hint=(0.15, 1)
        )
        self.add_widget(self.price_label)

    def increase_count(self, instance):
        new_count = self.cart_item["count"] + 1
        self.update_callback(self.index, new_count)

    def decrease_count(self, instance):
        new_count = self.cart_item["count"] - 1
        if new_count < 1:
            new_count = 1
        self.update_callback(self.index, new_count)

    def delete_item(self, instance):
        self.delete_callback(self.index)

# ----- 결제 페이지 -----
class PaymentScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(PaymentScreen, self).__init__(**kwargs)
        self.label = Label(
            text="카드를 삽입하여 주십시오",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.05,
            color=(255, 255, 255, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.3},
            halign='center',
            valign='middle'
        )
        self.layout.add_widget(self.label)

        # 카드 이미지 위젯 (overlay 중앙에 위치)
        self.card_image = Image(
            source="Source/Card.png",
            size_hint=(0.7, 0.7),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.overlay.add_widget(self.card_image)

    def on_enter(self):
        Window.bind(on_key_down=self._on_keyboard_down)
        self.start_camera()
        # 결제 시 장바구니 초기화
        self.manager.get_screen("cart").clear_cart()

    def on_leave(self):
        Window.unbind(on_key_down=self._on_keyboard_down)
        self.stop_camera()

    def update_camera(self, dt):
        if self.camera:
            ret, frame = self.camera.read()
            if ret:
                self.check_face_tracking(frame)

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

    def on_touch_down(self, touch):
        self.manager.current = "order"
        return True

# ----- 주문 발급 페이지 -----
class OrderIssuanceScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(OrderIssuanceScreen, self).__init__(**kwargs)
        self.order_label = Label(
            text="",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.09,
            color=(255, 255, 255, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.2},
            halign='center',
            valign='middle'
        )
        self.layout.add_widget(self.order_label)

    def on_enter(self):
        global order_number
        order_number += 1
        self.order_label.text = f"주문번호: {order_number}"
        Window.bind(on_key_down=self._on_keyboard_down)
        self.start_camera()

    def on_leave(self):
        Window.unbind(on_key_down=self._on_keyboard_down)
        self.stop_camera()

    def update_camera(self, dt):
        if self.camera:
            ret, frame = self.camera.read()
            if ret:
                self.check_face_tracking(frame)

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifier):
        if key == ord('a'):
            self.manager.current = "waiting"
        elif key == ord('q'):
            self.stop_camera()
            App.get_running_app().stop()
            sys.exit(0)
        return True

    def on_touch_down(self, touch):
        self.manager.current = "waiting"
        return True

# ----- ScreenManager 설정 -----
class KioskScreenManager(ScreenManager):
    def __init__(self, **kwargs):
        super(KioskScreenManager, self).__init__(**kwargs)
        self.transition = FadeTransition()
        # 필요 화면들을 등록
        self.add_widget(WaitingScreen(name="waiting"))
        self.add_widget(NewUserScreen(name="newuser"))
        self.add_widget(MenuDecisionScreen(name="menu"))
        self.add_widget(CartScreen(name="cart"))
        self.add_widget(PaymentScreen(name="payment"))
        self.add_widget(OrderIssuanceScreen(name="order"))

# ----- 전체 App 클래스 -----
class KioskApp(App):
    def build(self):
        return KioskScreenManager()

if __name__ == '__main__':
    KioskApp().run()