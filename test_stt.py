import sys
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.clock import Clock
from threading import Thread

from stt_whisper import record_and_transcribe
from server_api import send_to_server
from audio_player import play_audio_base64

# 한글 깨짐 방지
sys.stdout.reconfigure(encoding='utf-8')
Window.size = (500, 400)

FONT_PATH = "Source/NotoSansKR-Bold.ttf"

class STTBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 20
        self.spacing = 10

        self.log_area = TextInput(
            readonly=True,
            font_size=14,
            font_name=FONT_PATH,
            size_hint=(1, 0.7)
        )
        self.add_widget(self.log_area)

        self.stt_button = Button(
            text="🎤 STT 시작",
            font_size=20,
            font_name=FONT_PATH,
            size_hint=(1, 0.15)
        )
        self.stt_button.bind(on_press=self.run_stt)
        self.add_widget(self.stt_button)

        self.quit_button = Button(
            text="❌ 종료",
            font_size=16,
            font_name=FONT_PATH,
            size_hint=(1, 0.15)
        )
        self.quit_button.bind(on_release=lambda x: sys.exit(0))
        self.add_widget(self.quit_button)

    def log(self, message: str):
        Clock.schedule_once(lambda dt: self._append_log(message))

    def _append_log(self, message: str):
        self.log_area.text += f"{message}\n"
        self.log_area.cursor = (0, len(self.log_area.text.splitlines()))

    def run_stt(self, instance):
        self.log("🟡 버튼 눌림 - 음성 인식 시작")
        Thread(target=self.stt_thread).start()

    def stt_thread(self):
        try:
            self.log("🎧 마이크 듣는 중...")
            user_text = record_and_transcribe()
            self.log(f"📝 인식된 텍스트: {user_text}")

            self.log("📡 서버로 전송 중...")
            result = send_to_server(user_text)
            self.log(f"📨 서버 응답: {result}")

            if result:
                self.log(f"🤖 LLM 응답: {result.get('text', '')}")
                try:
                    play_audio_base64(result.get("audio_base64", ""))
                    self.log("🔊 음성 재생 완료")
                except Exception as e:
                    self.log(f"🔇 음성 재생 실패: {e}")
            else:
                self.log("❌ 서버 응답 없음")
        except Exception as e:
            self.log(f"❗ 예외 발생: {e}")

class STTApp(App):
    def build(self):
        return STTBox()

if __name__ == '__main__':
    STTApp().run()