"""
둥근 모서리 버튼 위젯
"""

from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from app.config import BOLD_FONT_PATH

class RoundedButton(Button):
    def __init__(self, **kwargs):
        super(RoundedButton, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (1, 1, 1, 0)
        self.font_name = BOLD_FONT_PATH
        self.color = (0, 0, 0, 1)
        with self.canvas.before:
            Color(252/255.0, 208/255.0, 41/255.0, 0.85)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[20, 20, 20, 20]
            )
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size 