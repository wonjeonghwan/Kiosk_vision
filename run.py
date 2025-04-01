"""
키오스크 애플리케이션 실행 파일
"""

from kivy.core.window import Window
from app.main import KioskApp

# 창 크기 설정
Window.size = (540, 900)

if __name__ == '__main__':
    KioskApp().run() 