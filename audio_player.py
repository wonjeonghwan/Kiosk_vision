import base64
import sounddevice as sd
import soundfile as sf
import io

def play_audio_base64(audio_base64_str):
    audio_bytes = base64.b64decode(audio_base64_str)
    with sf.SoundFile(io.BytesIO(audio_bytes)) as f:
        data = f.read(dtype='float32')
        sd.play(data, f.samplerate)
        sd.wait()
