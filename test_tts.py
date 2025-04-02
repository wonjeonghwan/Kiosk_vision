from google.cloud import texttospeech

def synthesize_text(text):
    # 클라이언트 초기화
    client = texttospeech.TextToSpeechClient()

    # 음성 합성 요청 설정
    input_text = texttospeech.SynthesisInput(text=text)

    # 음성 설정
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",  # 한국어
        ssml_gender=texttospeech.SsmlVoiceGender.MALE  # 성별 설정 (남성)
    )

    # 오디오 설정
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3  # MP3 포맷으로 음성 출력
    )

    # 음성 합성 요청
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )

    # 결과를 파일로 저장
    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
        print("Audio content written to file 'output.mp3'")

if __name__ == "__main__":
    text = "안녕하세요, Google Cloud Text-to-Speech API를 사용해 음성을 합성합니다."
    synthesize_text(text)
