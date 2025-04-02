class VADWhisperLoop:
    def __init__(self, callback, model_size="small", sample_rate=16000):
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
        self.processing_lock = threading.Lock()
        self.is_processing = False
        self.callback_lock = threading.Lock()
        self.is_callback_processing = False
        self.api_request_in_progress = False
        self.api_request_complete = threading.Event()  # API 요청 완료 이벤트 추가
        print("🔧 VADWhisperLoop 초기화 완료")

    def start(self):
        print("▶️ VADWhisperLoop 시작")
        self.running = True
        self.threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        print("⏹️ VADWhisperLoop 중지")
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
        # API 요청 중이거나 콜백 처리 중이면 음성 감지 중단
        if self.api_request_in_progress or self.is_callback_processing:
            if not self.api_request_complete.is_set():
                print("⏳ API 요청 대기 중 - 음성 감지 중단")
                return
                
        if self.is_processing:
            print("⏳ 처리 중 - 음성 감지 중단")
            return
            
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
        print("🔊 오디오 처리 시작")
        if len(self.audio_data) < self.min_voice_frames:
            print("🛑 무시할 정도로 짧은 음성")
            return

        with self.processing_lock:
            if self.is_processing:
                print("⏳ 이미 처리 중인 음성이 있습니다.")
                return
                
            self.is_processing = True
            try:
                print("🎯 STT 추론 시작")
                audio_np = self.np.concatenate(self.audio_data, axis=0).flatten().astype(self.np.float32) / 32768.0
                
                # 한국어와 영어만 처리하도록 설정
                result = self.model.transcribe(
                    audio_np,
                    fp16=False,
                    language="ko",  # 기본 언어를 한국어로 설정
                    task="transcribe",
                    # 한국어와 영어만 인식하도록 설정
                    condition_on_previous_text=False,  # 이전 텍스트에 의존하지 않음
                    temperature=0.0,  # 낮은 temperature로 더 정확한 인식
                    no_speech_threshold=0.6,  # 음성이 없을 가능성이 높은 경우 무시
                    logprob_threshold=-1.0,  # 낮은 확률의 인식 결과 무시
                    compression_ratio_threshold=2.4,  # 압축률이 높은 경우 무시
                )
                
                text = result.get("text", "").strip()
                print(f"📝 인식된 텍스트: {text}")
                
                if text and self.callback:
                    print("🔄 콜백 호출 시작")
                    self.threading.Thread(target=self._safe_callback, args=(text,), daemon=True).start()
                    
            except Exception as e:
                print(f"❌ 음성 처리 중 오류: {str(e)}")
            finally:
                self.is_processing = False
                print("✅ 오디오 처리 완료")

    def _safe_callback(self, text):
        """안전한 콜백 실행"""
        print("🔄 _safe_callback 시작")
        with self.callback_lock:
            if self.is_callback_processing:
                print("⏳ 이미 콜백이 처리 중입니다.")
                return
                
            self.is_callback_processing = True
            self.api_request_in_progress = True
            self.api_request_complete.clear()  # API 요청 시작 시 이벤트 초기화
            
            try:
                from kivy.clock import Clock
                print("⏰ Clock.schedule_once 호출")
                Clock.schedule_once(lambda dt: self._execute_callback(text))
            except Exception as e:
                print(f"❌ 콜백 실행 중 오류: {str(e)}")
            finally:
                self.is_callback_processing = False
                self.api_request_in_progress = False
                self.api_request_complete.set()  # API 요청 완료 시 이벤트 설정
                print("✅ _safe_callback 완료")

    def _execute_callback(self, text):
        """실제 콜백 실행"""
        try:
            self.callback(text)
        except Exception as e:
            print(f"❌ 콜백 실행 중 오류: {str(e)}")
        finally:
            self.api_request_complete.set()  # 콜백 실행 완료 시 이벤트 설정
