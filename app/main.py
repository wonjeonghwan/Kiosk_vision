"""
메인 앱
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from app.config import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE
from app.gui.screens.waiting_screen import WaitingScreen
from app.gui.screens.new_user_screen import NewUserScreen
from app.gui.screens.order_screen import OrderScreen
from app.gui.screens.payment_screen import PaymentScreen
from app.gui.screens.order_issuance_screen import OrderIssuanceScreen
import kivy
kivy.logger.Logger.setLevel("DEBUG")

class KioskApp(App):
    def build(self):
        """앱 화면 구성"""
        # 윈도우 설정
        self.title = WINDOW_TITLE
        self.icon = None  # TODO: 아이콘 추가
        
        # 화면 관리자 생성
        sm = ScreenManager()
        
        # 화면 등록
        sm.add_widget(WaitingScreen(name='waiting'))
        sm.add_widget(NewUserScreen(name='new_user'))
        sm.add_widget(OrderScreen(name='order'))
        sm.add_widget(PaymentScreen(name='payment'))
        sm.add_widget(OrderIssuanceScreen(name='order_issuance'))
        
        return sm

if __name__ == '__main__':
    KioskApp().run() 