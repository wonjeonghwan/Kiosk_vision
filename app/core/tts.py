"""
텍스트를 음성으로 변환하는 TTS 모듈
"""

import os
import threading
import tempfile
import glob
import time
import subprocess
from pydub import AudioSegment

# Google Cloud TTS 대신 gTTS 사용
try:
    from gtts import gTTS
    USE_GTTS = True
    print("✅ gTTS 라이브러리 사용")
except ImportError:
    USE_GTTS = False
    print("⚠️ gTTS 라이브러리를 찾을 수 없습니다. pip install gTTS로 설치하세요.")
    
# Google Cloud TTS는 선택적으로 사용
try:
    from google.cloud import texttospeech
    USE_GOOGLE_CLOUD = True
    print("✅ Google Cloud TTS 라이브러리 사용 가능")
except ImportError:
    USE_GOOGLE_CLOUD = False
    print("⚠️ Google Cloud TTS 라이브러리를 찾을 수 없습니다.")

# playsound 라이브러리 사용
try:
    from playsound import playsound
    USE_PLAYSOUND = True
    print("✅ playsound 라이브러리 사용")
except ImportError:
    USE_PLAYSOUND = False
    print("⚠️ playsound 라이브러리를 찾을 수 없습니다. pip install playsound로 설치하세요.")

class TTSManager:
    """TTS 관리 클래스"""
    
    def __init__(self):
        """TTS 초기화"""
        # 애플리케이션 전용 디렉토리 설정
        self.app_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        self.audio_dir = os.path.join(self.app_dir, "audio")
        
        # 디렉토리가 없으면 생성
        if not os.path.exists(self.app_dir):
            os.makedirs(self.app_dir)
            print(f"✅ 애플리케이션 디렉토리 생성: {self.app_dir}")
            
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
            print(f"✅ 오디오 디렉토리 생성: {self.audio_dir}")
            
        self.temp_dir = self.audio_dir  # 임시 디렉토리 대신 오디오 디렉토리 사용
        self.play_lock = threading.Lock()
        self.is_playing = False
        
        # Google Cloud TTS 초기화 (선택적)
        if USE_GOOGLE_CLOUD:
            self._init_google_cloud_tts()
        else:
            self.client = None
            self.voice = None
            self.audio_config = None
            
        print("🔊 TTSManager 초기화 완료")
        
        # 초기화 후 테스트 음성 생성
        # self._test_tts()
            
    def _init_google_cloud_tts(self):
        """Google Cloud TTS 초기화"""
        try:
            # 인증 정보 설정
            config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
            credentials_path = self._find_credentials_file(config_dir)
            
            if credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                print(f"✅ Google 인증 정보 설정 완료: {credentials_path}")
            else:
                print(f"⚠️ Google 인증 정보 파일을 찾을 수 없습니다.")
                print("⚠️ Google Cloud TTS 기능이 작동하지 않을 수 있습니다.")
                
            self.client = texttospeech.TextToSpeechClient()
            self.voice = texttospeech.VoiceSelectionParams(
                language_code="ko-KR",  # 한국어
                ssml_gender=texttospeech.SsmlVoiceGender.MALE  # 성별 설정 (남성)
            )
            self.audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3  # MP3 포맷으로 음성 출력
            )
        except Exception as e:
            print(f"❌ Google Cloud TTS 초기화 중 오류: {str(e)}")
            self.client = None
            self.voice = None
            self.audio_config = None
            
    def _find_credentials_file(self, config_dir):
        """인증 파일 찾기"""
        # 가능한 파일 이름 목록
        possible_names = [
            "google_credentials.json",
            "credentials.json",
            "service-account.json",
            "google-service-account.json"
        ]
        
        # 정확한 이름으로 찾기
        for name in possible_names:
            path = os.path.join(config_dir, name)
            if os.path.exists(path):
                return path
                
        # 와일드카드로 찾기 (모든 JSON 파일)
        json_files = glob.glob(os.path.join(config_dir, "*.json"))
        if json_files:
            # 가장 최근에 수정된 파일 선택
            return max(json_files, key=os.path.getmtime)
            
        return None
        
    def _test_tts(self):
        """TTS 기능 테스트"""
        try:
            print("🔊 TTS 기능 테스트 시작")
            test_text = "안녕하세요. TTS 테스트입니다."
            test_file_mp3 = os.path.join(self.temp_dir, "tts_test.mp3")
            test_file_wav = os.path.join(self.temp_dir, "tts_test.wav")
            
            # 음성 합성
            if USE_GOOGLE_CLOUD and self.client:
                # Google Cloud TTS 사용
                input_text = texttospeech.SynthesisInput(text=test_text)
                response = self.client.synthesize_speech(
                    input=input_text, 
                    voice=self.voice, 
                    audio_config=self.audio_config
                )
                
                # 파일 저장
                with open(test_file_mp3, "wb") as out:
                    out.write(response.audio_content)
            elif USE_GTTS:
                # gTTS 사용
                tts = gTTS(text=test_text, lang='ko')
                tts.save(test_file_mp3)
            else:
                print("❌ 사용 가능한 TTS 라이브러리가 없습니다.")
                return
                
            # MP3를 WAV로 변환
            audio = AudioSegment.from_mp3(test_file_mp3)
            audio.export(test_file_wav, format="wav")
                
            print(f"✅ 테스트 음성 파일 생성 완료: {test_file_wav}")
            
            # 음성 재생 (별도 스레드에서)
            threading.Thread(target=self._play_test_audio, args=(test_file_wav,)).start()
            
        except Exception as e:
            print(f"❌ TTS 테스트 중 오류: {str(e)}")
            
    def _play_test_audio(self, audio_file):
        """테스트 음성 재생"""
        try:
            time.sleep(1)  # 잠시 대기
            print(f"▶️ 테스트 음성 재생 시작: {audio_file}")
            
            # playsound로 오디오 재생
            if USE_PLAYSOUND:
                playsound(audio_file)
            else:
                # 대체 방법: 시스템 기본 플레이어로 재생
                if os.name == 'nt':  # Windows
                    os.startfile(audio_file)
                else:  # macOS, Linux
                    subprocess.call(('open', audio_file))
                
            print("✅ 테스트 음성 재생 완료")
        except Exception as e:
            print(f"❌ 테스트 음성 재생 중 오류: {str(e)}")
        
    def synthesize(self, text, save_path=None):
        """텍스트를 음성으로 변환"""
        try:
            print(f"🔊 음성 합성 시작: {text[:20]}...")
            
            # 임시 파일 경로 설정
            if save_path is None:
                save_path_mp3 = os.path.join(self.temp_dir, "tts_output.mp3")
                save_path_wav = os.path.join(self.temp_dir, "tts_output.wav")
            else:
                save_path_mp3 = save_path.replace(".wav", ".mp3")
                save_path_wav = save_path
                
            # Google Cloud TTS 사용 (가능한 경우)
            if USE_GOOGLE_CLOUD and self.client:
                print("🔊 Google Cloud TTS 사용")
                input_text = texttospeech.SynthesisInput(text=text)
                response = self.client.synthesize_speech(
                    input=input_text, 
                    voice=self.voice, 
                    audio_config=self.audio_config
                )
                
                # 파일 저장
                with open(save_path_mp3, "wb") as out:
                    out.write(response.audio_content)
            # gTTS 사용 (대체 방법)
            elif USE_GTTS:
                print("🔊 gTTS 사용")
                try:
                    print(f"🔊 gTTS 음성 생성 시작: {save_path_mp3}")
                    tts = gTTS(text=text, lang='ko')
                    print(f"🔊 gTTS 음성 생성 완료: {save_path_mp3}")
                    tts.save(save_path_mp3)
                    print("✅ gTTS 음성 생성 완료")
                except Exception as e:
                    print(f"❌ gTTS 사용 중 오류: {str(e)}")
                    return None
            else:
                print("❌ 사용 가능한 TTS 라이브러리가 없습니다.")
                return None
                
            # MP3를 WAV로 변환
            try:
                audio = AudioSegment.from_mp3(save_path_mp3)
                audio.export(save_path_wav, format="wav")
                print("✅ MP3를 WAV로 변환 완료")
            except Exception as e:
                print(f"❌ MP3를 WAV로 변환 중 오류: {str(e)}")
                return None
                
            print(f"✅ 음성 파일 저장 완료: {save_path_wav}")
            return save_path_wav
            
        except Exception as e:
            print(f"❌ 음성 합성 중 오류: {str(e)}")
            return None
            
    def play_audio(self, audio_path=None, text=None):
        """음성 재생"""
        try:
            with self.play_lock:
                if self.is_playing:
                    print("⏳ 이미 재생 중입니다.")
                    return
                    
                self.is_playing = True
                
                # 텍스트가 제공된 경우 음성 합성 후 재생
                if text:
                    audio_path = self.synthesize(text)
                    
                if audio_path and os.path.exists(audio_path):
                    print(f"▶️ 음성 재생 시작: {audio_path}")
                    
                    # playsound로 오디오 재생
                    if USE_PLAYSOUND:
                        playsound(audio_path)
                    else:
                        # 대체 방법: 시스템 기본 플레이어로 재생
                        if os.name == 'nt':  # Windows
                            os.startfile(audio_path)
                        else:  # macOS, Linux
                            subprocess.call(('open', audio_path))
                        
                    print("✅ 음성 재생 완료")
                else:
                    print("❌ 재생할 음성 파일이 없습니다.")
                    
        except Exception as e:
            print(f"❌ 음성 재생 중 오류: {str(e)}")
        finally:
            self.is_playing = False
            
    def play_async(self, text):
        """비동기로 음성 재생"""
        threading.Thread(target=self.play_audio, args=(None, text)).start()
        
# 싱글톤 인스턴스 생성
tts_manager = TTSManager()

# 편의 함수
def synthesize_text(text, save_path=None):
    """텍스트를 음성으로 변환"""
    return tts_manager.synthesize(text, save_path)
    
def play_text(text):
    """텍스트를 음성으로 재생"""
    tts_manager.play_async(text)
    
# 직접 실행 시 테스트
if __name__ == "__main__":
    print("🔊 TTS 모듈 테스트 시작")
    test_text = "안녕하세요. 이것은 TTS 테스트입니다."
    play_text(test_text)
    print("✅ TTS 모듈 테스트 완료")

