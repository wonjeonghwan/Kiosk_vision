"""
채팅 말풍선 위젯
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
from kivy.animation import Animation
from app.config import BOLD_FONT_PATH

class ChatBubble(BoxLayout):
    def __init__(self, sender, text, **kwargs):
        super(ChatBubble, self).__init__(**kwargs)
        # (1) Bubble 전체에 대한 설정: 세로 크기는 자동, 가로 방향 배치
        self.orientation = 'horizontal'
        self.size_hint_y = None
        # (2) Bubble 자체의 패딩/간격을 통일
        #    LLM/USER 구분 없이 동일한 바깥 여백을 갖도록 함
        self.padding = (10, 5, 10, 5)
        self.spacing = 5

        # (3) 실제 메시지 Label 생성
        self.label = Label(
            text=text,
            font_name=BOLD_FONT_PATH,
            font_size=Window.height * 0.02,
            color=(0, 0, 0, 1),
            # Label 내부에서 줄바꿈과 정렬을 적용하기 위해 text_size를 지정
            size_hint=(None, None),
            text_size=(Window.width * 0.55, None),
            valign='middle'  # 세로 정렬
        )
        self.label.bind(texture_size=self.update_label_size)
        self.label.bind(pos=self.update_rect_bg, size=self.update_rect_bg)

        # (4) 말풍선 배경: RoundedRectangle
        #    (LLM과 USER 둘 다 동일한 방법으로 AnchorLayout에 넣고
        #     anchor_x만 다르게 해서 좌우 정렬만 달리 함)
        if sender == "LLM":
            # LLM: 왼쪽 정렬
            self.label.halign = "left"
            with self.label.canvas.before:
                Color(0.9, 0.9, 0.9, 1)
                self.rect_bg = RoundedRectangle(radius=[10, 10, 10, 10])

            # AnchorLayout으로 감싸서 왼쪽 정렬
            anchor = AnchorLayout(
                size_hint_x=1,
                anchor_x='left',   # 왼쪽 정렬
                padding=(0, 0, 0, 0)
            )
            anchor.add_widget(self.label)
            self.add_widget(anchor)

        else:
            # USER: 오른쪽 정렬
            self.label.halign = "right"
            with self.label.canvas.before:
                Color(1, 1, 0.8, 1)
                self.rect_bg = RoundedRectangle(radius=[10, 10, 10, 10])

            # AnchorLayout으로 감싸서 오른쪽 정렬
            anchor = AnchorLayout(
                size_hint_x=1,
                anchor_x='right',  # 오른쪽 정렬
                padding=(0, 0, 0, 0)
            )
            anchor.add_widget(self.label)
            self.add_widget(anchor)

        # (5) 새로 생성될 때 높이를 0으로 시작 -> 애니메이션으로 자연스럽게 확대
        self.height = 0

    def update_label_size(self, instance, texture_size):
        """Label의 실제 텍스트 크기에 따라 말풍선 크기 갱신"""
        new_width = texture_size[0] + 20
        new_height = texture_size[1] + 20
        self.label.size = (new_width, new_height)

        # 첫 등장 시 높이를 0 -> new_height로 애니메이션
        if self.height == 0:
            Animation(height=new_height, duration=0.3, t='out_quad').start(self)
        else:
            self.height = new_height

    def update_rect_bg(self, *args):
        """라벨 위치/크기에 따라 말풍선 배경도 갱신"""
        self.rect_bg.pos = self.label.pos
        self.rect_bg.size = self.label.size 