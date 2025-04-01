# from threading import Thread
# from kivy.clock import Clock
# from stt_whisper import record_and_transcribe
# from server_api import send_to_server
# from audio_player import play_audio_base64

# def start_full_pipeline():
#     Thread(target=run_pipeline).start()

# def run_pipeline():
#     # 1. 사용자 음성 → 텍스트
#     user_text = record_and_transcribe()
#     print("🎤 인식된 텍스트:", user_text)

#     # 2. 텍스트 → 서버 전송 → LLM 응답 + 음성(base64)
#     result = send_to_server(user_text)
#     if result:
#         llm_text = result.get("text", "")
#         audio_base64 = result.get("audio_base64", "")
#         print("🤖 LLM 응답:", llm_text)

#         # 3. 음성 재생
#         play_audio_base64(audio_base64)

#         # (선택) Kivy UI에 텍스트 표시하고 싶다면 Clock.schedule_once로 추가 가능



# from kivy.app import App
# from kivy.uix.boxlayout import BoxLayout
# from kivy.uix.button import Button
# from kivy.core.window import Window
# from threading import Thread
# import sys

# # STT 함수: Whisper 관련 모듈 불러오기 (예시)
# def dummy_stt():
#     print("🎙️ 녹음 시작", flush=True)
#     import time
#     time.sleep(2)
#     print("📝 인식된 텍스트: 안녕하세요", flush=True)

# # 창 사이즈 강제 지정
# Window.size = (400, 300)

# class STTBox(BoxLayout):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.orientation = "vertical"
#         self.padding = 30
#         self.spacing = 20

#         self.stt_button = Button(text="🎤 STT 시작", font_size=24)
#         self.stt_button.bind(on_release=self.run_stt)
#         self.add_widget(self.stt_button)

#         self.quit_button = Button(text="❌ 종료", font_size=18)
#         self.quit_button.bind(on_release=lambda x: sys.exit(0))
#         self.add_widget(self.quit_button)

#     def run_stt(self, instance):
#         Thread(target=self.stt_thread).start()

#     def stt_thread(self):
#         dummy_stt()

# class STTApp(App):
#     def build(self):
#         return STTBox()

# if __name__ == '__main__':
#     STTApp().run()


from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from threading import Thread
import sys

from stt_whisper import record_and_transcribe
from server_api import send_to_server
from audio_player import play_audio_base64

Window.size = (400, 300)

class STTBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 30
        self.spacing = 20

        self.stt_button = Button(text="🎤 STT 시작", font_size=24)
        self.stt_button.bind(on_release=self.run_stt)
        self.add_widget(self.stt_button)

        self.quit_button = Button(text="❌ 종료", font_size=18)
        self.quit_button.bind(on_release=lambda x: sys.exit(0))
        self.add_widget(self.quit_button)

    def run_stt(self, instance):
        Thread(target=self.stt_thread).start()

    def stt_thread(self):
        print("🎧 사용자 음성 듣는 중...", flush=True)
        user_text = record_and_transcribe()
        print(f"📝 인식된 텍스트: {user_text}", flush=True)

        print("📡 서버로 전송 중...", flush=True)
        result = send_to_server(user_text)

        if result:
            print("🤖 LLM 응답:", result["text"], flush=True)
            play_audio_base64(result["audio_base64"])
        else:
            print("❌ 서버 응답 없음")

class STTApp(App):
    def build(self):
        return STTBox()

if __name__ == '__main__':
    STTApp().run()
