import sys
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.clock import Clock

# 윈도우 기본 한글 폰트 경로
SYSTEM_FONT_PATH = "C:/Windows/Fonts/malgun.ttf"

# 전역 변수: 주문번호 (발급페이지 노출 시마다 1씩 증가)
order_number = 0

# 인식된 사용자 이름 (실제 얼굴인식 결과와 연동 시 활용)
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
        
        # 안내 라벨 (창 크기에 비례하는 폰트 크기)
        self.info_label = Label(
            text="대기중...\n(a 버튼을 눌러 얼굴인식 시작)",
            font_name=SYSTEM_FONT_PATH,
            font_size=Window.height * 0.03,  # 창 높이의 3%로 조정
            color=(255, 255, 255, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.15}  # 위치를 약간 위로 조정
        )
        self.layout.add_widget(self.info_label)
        self.add_widget(self.layout)

    def on_enter(self):
        # 대기화면 진입 시 얼굴인식 시뮬레이션(실제 구현 시 main.py 연동)
        # 5초 후 simulate_face_recognition() 호출
        Window.bind(on_key_down=self._on_keyboard_down)

    def on_leave(self):
        Window.unbind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifier):
        if key == ord('a'):
            self.manager.current = "menu"
        elif key == ord('q'):
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
            font_size=Window.height * 0.03,  # 창 높이의 3%
            color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.layout.add_widget(self.label)
        self.add_widget(self.layout)

    def on_enter(self):
        Window.bind(on_key_down=self._on_keyboard_down)

    def on_leave(self):
        Window.unbind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifier):
        if key == ord('a'):
            self.manager.current = "payment"
        elif key == ord('s'):
            self.manager.current = "waiting"
        elif key == ord('q'):
            App.get_running_app().stop()
            sys.exit(0)
        return True

class PaymentScreen(Screen):
    """결제화면"""
    def __init__(self, **kwargs):
        super(PaymentScreen, self).__init__(**kwargs)
        self.layout = FloatLayout()
        
        # 결제 라벨
        self.label = Label(
            text="결제",
            font_name=SYSTEM_FONT_PATH,
            font_size=Window.height * 0.03,  # 창 높이의 3%
            color=(1, 0, 0, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        # 안내 라벨
        self.info = Label(
            text="(a 버튼을 눌러 진행,\n s 버튼을 누르면 대기화면으로)",
            font_name=SYSTEM_FONT_PATH,
            font_size=Window.height * 0.025,  # 창 높이의 2.5%
            color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.2}
        )
        
        self.layout.add_widget(self.label)
        self.layout.add_widget(self.info)
        self.add_widget(self.layout)

    def on_enter(self):
        Window.bind(on_key_down=self._on_keyboard_down)

    def on_leave(self):
        Window.unbind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifier):
        if key == ord('a'):
            self.manager.current = "order"
        elif key == ord('s'):
            self.manager.current = "waiting"
        elif key == ord('q'):
            App.get_running_app().stop()
            sys.exit(0)
        return True

class OrderIssuanceScreen(Screen):
    """주문번호 발급 페이지"""
    def __init__(self, **kwargs):
        super(OrderIssuanceScreen, self).__init__(**kwargs)
        self.layout = FloatLayout()
        
        # 주문번호 라벨
        self.order_label = Label(
            text="",
            font_name=SYSTEM_FONT_PATH,
            font_size=Window.height * 0.03,  # 창 높이의 3%
            color=(0, 1, 0, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        # 안내 라벨
        self.info = Label(
            text="(a 버튼을 눌러 처음으로)",
            font_name=SYSTEM_FONT_PATH,
            font_size=Window.height * 0.025,  # 창 높이의 2.5%
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
        Window.bind(on_key_down=self._on_keyboard_down)

    def on_leave(self):
        Window.unbind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, window, key, scancode, codepoint, modifier):
        if key == ord('a'):
            self.manager.current = "waiting"
        elif key == ord('q'):
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

    def on_stop(self):
        # 앱 종료 시 필요한 정리 작업
        pass

if __name__ == '__main__':
    KioskApp().run()