"""
장바구니 관련 위젯
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from app.config import BOLD_FONT_PATH, LIGHT_FONT_PATH
from .touch_keyboard import RoundedButton

# ----- 얇은 구분선 위젯 (가로길이 50%, 가운데 정렬) -----
class DividerLine(BoxLayout):
    def __init__(self, **kwargs):
        super(DividerLine, self).__init__(**kwargs)
        self.size_hint = (0.5, None)
        self.height = 1
        self.pos_hint = {'center_x': 0.5}
        with self.canvas:
            Color(0, 0, 0, 0.5)
            self.rect = Rectangle(pos=self.pos, size=(0, 0))
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = (self.width, self.height)

# ----- 장바구니 항목 위젯 -----
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
        
        # 이미지 컨테이너
        self.image_container = AnchorLayout(
            size_hint=(0.15, 1),
            anchor_x='center',
            anchor_y='center',
            padding=(10, 5, 10, 5)
        )
        self.image = Image(
            source=cart_item["image"],
            size_hint=(None, None),
            size=(145, 145),
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
        
        # 수량
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