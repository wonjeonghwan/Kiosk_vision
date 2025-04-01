"""
터치 키보드 위젯
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from app.config import BOLD_FONT_PATH, LIGHT_FONT_PATH
from .rounded_button import RoundedButton

class TouchKeyboard(BoxLayout):
    def __init__(self, callback, **kwargs):
        super(TouchKeyboard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 0
        self.padding = 1
        self.callback = callback
        self.cho = ''
        self.jung = ''
        self.jong = ''
        self.shift_mode = False
        self.key_mapping = {
            'ㄱ': 'ㄲ', 'ㄷ': 'ㄸ', 'ㅂ': 'ㅃ', 'ㅅ': 'ㅆ', 'ㅈ': 'ㅉ',
            'ㅐ': 'ㅒ', 'ㅔ': 'ㅖ'
        }
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
        self.key_buttons = []
        for row_keys in self.normal_keys:
            row_layout = BoxLayout(spacing=1)
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
        special_row = BoxLayout(spacing=1)
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
        self.shift_btn.background_color = (252/255.0, 208/255.0, 41/255.0, 0.85) if self.shift_mode else (200/255.0, 200/255.0, 200/255.0, 0.85)
        for row_idx, row_buttons in enumerate(self.key_buttons):
            for btn_idx, btn in enumerate(row_buttons):
                btn.text = self.shift_keys[row_idx][btn_idx] if self.shift_mode else self.normal_keys[row_idx][btn_idx]

    def on_key_press(self, key):
        if self.shift_mode and key in self.key_mapping:
            key = self.key_mapping[key]
            self.shift_mode = False
            self.toggle_shift_mode()
        if key == '스페이스':
            if self.cho or self.jung or self.jong:
                combined = self.combine_jamo()
                if combined:
                    self.callback(combined)
                self.cho = self.jung = self.jong = ''
            self.callback(' ')
        elif key == '백스페이스':
            if self.jong:
                self.jong = ''
                combined = self.combine_jamo()
                if combined:
                    self.callback('backspace')
                    self.callback(combined)
            elif self.jung:
                self.jung = ''
                if self.cho:
                    self.callback('backspace')
                    self.callback(self.cho)
            elif self.cho:
                self.cho = ''
                self.callback('backspace')
            else:
                self.callback('backspace')
        elif key == '엔터':
            if self.cho or self.jung or self.jong:
                combined = self.combine_jamo()
                if combined:
                    self.callback('backspace')
                    self.callback(combined)
                self.cho = self.jung = self.jong = ''
            self.callback('enter')
        else:
            CONSONANTS = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
            VOWELS = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
            if key in CONSONANTS:
                if not self.cho:
                    self.cho = key
                    self.callback(key)
                elif not self.jung:
                    self.callback('backspace')
                    self.cho = key
                    self.callback(key)
                elif not self.jong:
                    self.jong = key
                    combined = self.combine_jamo()
                    if combined:
                        self.callback('backspace')
                        self.callback(combined)
                else:
                    combined = self.combine_jamo()
                    if combined:
                        self.callback('backspace')
                        self.callback(combined)
                    self.cho = key
                    self.jung = self.jong = ''
                    self.callback(key)
            elif key in VOWELS:
                if not self.cho:
                    self.callback(key)
                elif not self.jung:
                    self.jung = key
                    combined = self.combine_jamo()
                    if combined:
                        self.callback('backspace')
                        self.callback(combined)
                else:
                    combined = self.combine_jamo()
                    if combined:
                        self.callback('backspace')
                        self.callback(combined)
                    self.cho = ''
                    self.jung = key
                    self.jong = ''
                    self.callback(key)

    def combine_jamo(self):
        if not self.cho or not self.jung:
            return None
        CHO = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        JUNG = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
        JONG = ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
        try:
            cho_idx = CHO.index(self.cho)
            jung_idx = JUNG.index(self.jung)
            jong_idx = JONG.index(self.jong) if self.jong else 0
            unicode_value = 0xAC00 + cho_idx * 21 * 28 + jung_idx * 28 + jong_idx
            return chr(unicode_value)
        except ValueError:
            return None 