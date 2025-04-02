class VADWhisperLoop:
    def __init__(self, callback, model_size="base", sample_rate=16000):
        import whisper
        import webrtcvad
        import numpy as np
        import sounddevice as sd
        import collections
        import threading

        self.callback = callback
        self.model = whisper.load_model(model_size)
        self.vad = webrtcvad.Vad(1)
        self.sd = sd
        self.np = np
        self.collections = collections
        self.threading = threading

        self.running = False
        self.sample_rate = sample_rate
        self.frame_duration = 30  # ms
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
        self.max_silence = int(1000 / self.frame_duration)
        self.min_voice_frames = 5
        self.audio_data = []
        self.silence_counter = 0
        self.triggered = False

    def start(self):
        self.running = True
        self.threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self.running = False

    def _run(self):
        print("🎤 VAD STT 루프 시작")
        try:
            with self.sd.InputStream(channels=1, samplerate=self.sample_rate, dtype='int16',
                                     blocksize=self.frame_size, callback=self._audio_callback):
                while self.running:
                    self.sd.sleep(100)
        except Exception as e:
            print("❌ VAD 루프 오류:", e)

    def _audio_callback(self, indata, frames, time_info, status):
        audio_bytes = indata.tobytes()
        is_speech = self.vad.is_speech(audio_bytes, self.sample_rate)

        if is_speech:
            if not self.triggered:
                self.triggered = True
                print("🎙 음성 감지 시작")
            self.audio_data.append(indata.copy())
            self.silence_counter = 0
        else:
            if self.triggered:
                self.silence_counter += 1
                if self.silence_counter > self.max_silence:
                    self.triggered = False
                    print("🔇 음성 종료 - 추론 시작")
                    self._process_audio()
                    self.audio_data.clear()
                    self.silence_counter = 0

    def _process_audio(self):
        if len(self.audio_data) < self.min_voice_frames:
            print("🛑 무시할 정도로 짧은 음성")
            return

        audio_np = self.np.concatenate(self.audio_data, axis=0).flatten().astype(self.np.float32) / 32768.0
        result = self.model.transcribe(audio_np, fp16=False, language="ko")
        text = result.get("text", "").strip()
        if text and self.callback:
            try:
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self.callback(text))
            except Exception:
                self.callback(text)
