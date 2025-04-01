"""
주문 화면
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
import cv2
import numpy as np
from kivy.core.image import Texture
from kivy.graphics.texture import Texture
from app.config import BOLD_FONT_PATH, BACK_IMG, LOGO_IMG, CHARACTER_IMG
from app.core.dummy_data import OrderData, ChatDummy
from app.gui.widgets import RoundedButton, CartItemWidget, DividerLine, ChatBubble
from .base_screen import BaseScreen
from app.core.face_detection import extract_face_embeddings, track_target_face, find_best_match, initialize_database, MAX_LOST_FRAMES
from PIL import Image as PILImage, ImageDraw, ImageFont
import sqlite3
import time

class OrderScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(OrderScreen, self).__init__(**kwargs)
        
        # 다음 화면 설정
        self.next_screen = "payment"
        
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
            text="주문 확인",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.03,
            color=(0, 0, 0, 1),
            pos_hint={'center_x': 0.5, 'top': 1.44},
            halign='center',
            valign='middle'
        )
        self.overlay.add_widget(self.title_label)
        
        # 채팅 영역 추가 (위쪽으로 이동)
        self.chat_scroll = ScrollView(
            size_hint=(0.9, 0.45),
            pos_hint={'center_x': 0.5, 'top': 1.5},
            bar_width=6,
            bar_color=(252/255.0, 208/255.0, 41/255.0, 0.85),
            bar_inactive_color=(252/255.0, 208/255.0, 41/255.0, 0.5)
        )
        self.chat_box = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=10,
            padding=10
        )
        self.chat_box.bind(minimum_height=self.chat_box.setter('height'))
        self.chat_scroll.add_widget(self.chat_box)
        
        # 채팅 영역 배경 (노란색 테두리)
        with self.chat_scroll.canvas.before:
            Color(252/255.0, 208/255.0, 41/255.0, 0.5)
            self.chat_border = RoundedRectangle(pos=self.chat_scroll.pos, size=self.chat_scroll.size, radius=[20, 20, 20, 20])
        self.chat_scroll.bind(pos=lambda inst, val: setattr(self.chat_border, 'pos', val),
                            size=lambda inst, val: setattr(self.chat_border, 'size', val))
        self.overlay.add_widget(self.chat_scroll)
        
        # 스크롤뷰 (장바구니 목록 - 하단으로 이동)
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
        
        # 하단 바: 결제하기 버튼과 총 금액
        self.bottom_bar = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.15),
            pos_hint={'x': 0, 'y': 0.08},
            spacing=10,
            padding=[10, 5]
        )
        self.pay_button = RoundedButton(
            text="결제하기",
            font_name=BOLD_FONT_PATH,
            font_size=37,
            size_hint=(0.3, 0.8)
        )
        self.total_label = Label(
            text="총 금액: 0원",
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.035,
            color=(0, 0, 0, 1),
            halign='center',
            valign='middle',
            size_hint=(0.4, 1)
        )
        self.bottom_bar.add_widget(self.pay_button)
        self.bottom_bar.add_widget(self.total_label)
        self.overlay.add_widget(self.bottom_bar)
        
        # 레이아웃에 오버레이 추가
        self.layout.add_widget(self.overlay)
        
        # 메인 레이아웃을 화면에 추가
        self.add_widget(self.layout)
        
        # 장바구니 데이터
        self.cart_items = OrderData.get_dummy_order_data()
        self.pay_button.bind(on_release=self.proceed_to_payment)
        self.refresh_cart_view()
        
        # 대화 메시지 더미 배열
        self.chat_messages = ChatDummy.get_chat_sequence()
        self.chat_index = 0
        self.chat_event = None

    def refresh_cart_view(self):
        """장바구니 목록 새로고침"""
        self.cart_box.clear_widgets()
        for idx, item in enumerate(self.cart_items):
            widget = CartItemWidget(
                cart_item=item,
                index=idx,
                update_callback=self.update_cart_item,
                delete_callback=self.delete_cart_item
            )
            self.cart_box.add_widget(widget)
            if idx < len(self.cart_items) - 1:
                divider = DividerLine()
                self.cart_box.add_widget(divider)
        total = sum(i["price"] * i["count"] for i in self.cart_items)
        self.total_label.text = f"총 금액: {total}원"

    def update_cart_item(self, index, new_count):
        """장바구니 항목 수량 업데이트"""
        if 0 <= index < len(self.cart_items):
            self.cart_items[index]["count"] = new_count
            self.refresh_cart_view()

    def delete_cart_item(self, index):
        """장바구니 항목 삭제"""
        if 0 <= index < len(self.cart_items):
            del self.cart_items[index]
            self.refresh_cart_view()

    def proceed_to_payment(self, instance):
        """결제 화면으로 이동"""
        self.manager.current = "payment"

    def clear_cart(self):
        """장바구니 비우기"""
        self.cart_items = []
        self.refresh_cart_view()

    def on_enter(self):
        """화면 진입 시 호출"""
        self.start_camera()
        # 스케줄러를 시작해서 3초마다 하나씩 대화 추가
        self.chat_index = 0
        self.chat_box.clear_widgets()
        self.chat_event = Clock.schedule_interval(self.add_next_chat_message, 3.0)

    def on_leave(self):
        """화면 이탈 시 호출"""
        self.stop_camera()
        if self.chat_event:
            self.chat_event.cancel()

    def add_next_chat_message(self, dt):
        """다음 채팅 메시지 추가"""
        if self.chat_index < len(self.chat_messages):
            msg = self.chat_messages[self.chat_index]
            bubble = ChatBubble(msg['sender'], msg['text'])
            self.chat_box.add_widget(bubble)
            # 스크롤 맨 아래로 이동
            Animation(scroll_y=0, duration=0.3, t='out_quad').start(self.chat_scroll)
            self.chat_index += 1
        else:
            # 모든 메시지 추가 후 스케줄러 취소
            if self.chat_event:
                self.chat_event.cancel()

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
        # 자식 위젯의 터치 이벤트 먼저 처리
        for child in self.children:
            if child.collide_point(*touch.pos):
                return child.on_touch_down(touch)
        
        # 화면 전환
        self.manager.current = self.next_screen
        return True 