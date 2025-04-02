"""
키오스크 애플리케이션 실행 파일
"""
import sys
import traceback
from kivy.core.window import Window
from app.main import KioskApp
from kivy.logger import Logger

Logger.setLevel("DEBUG")
def handle_exception(exc_type, exc_value, exc_traceback):
    print("❌ 전역 예외 발생:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

# 창 크기 설정
Window.size = (540, 900)

if __name__ == '__main__':
    try:
        KioskApp().run() 
    except Exception as e:
        print("❌ 앱 실행 중 예외 발생!")
        traceback.print_exc()  # 전체 에러 로그 출력
        input("⚠️ 오류 확인 후 Enter 키를 누르세요...")