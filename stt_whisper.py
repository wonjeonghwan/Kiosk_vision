import whisper
import sounddevice as sd
import numpy as np
import tempfile
import scipy.io.wavfile
import os

print("Whisper 모델 로딩 중...", flush=True)
model = whisper.load_model("base")
print("Whisper 모델 로드 완료", flush=True)

def record_and_transcribe(duration=4):
    print("STT 함수 진입", flush=True)

    sr = 16000
    print("마이크 녹음 시작", flush=True)
    recording = sd.rec(int(duration * sr), samplerate=sr, channels=1, dtype='int16')
    sd.wait()
    print("녹음 완료", flush=True)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        scipy.io.wavfile.write(f.name, sr, recording)
        print("Whisper 추론 중...", flush=True)
        result = model.transcribe(f.name, language='ko')
        # print("Whisper 결과:", result["text"], flush=True)
        print("Whisper 결과:", result["text"])
        f.close()
        os.remove(f.name)
        return result["text"]