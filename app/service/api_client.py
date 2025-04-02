"""
FastAPI 서버와 통신 
"""

import requests
import base64

API_BASE = "http://192.168.10.70:8080"

### 신규 사용자 등록
def register_user(name: str, phone: str, face_encoding: str) -> dict:
    """신규 사용자 등록"""
    try:
        b64_encoding_face = base64.b64encode(face_encoding.tobytes()).decode("utf-8")
        data = {
            "name": name,
            "phone": phone,
            "face_encoding": b64_encoding_face
        }
        res = requests.post(f"{API_BASE}/users/", json=data)
        return res.json()
    except Exception as e:
        print(f"[register_user ERROR] {e}")
        return {"status": "error", "message": str(e)}
    
### 기존 사용자 업데이트 
def update_user(user_id:int, name: str, phone: str, face_encoding: str) -> dict:
    """TODO : 사용자 업데이트 추후 개선"""
    try:
        b64_encoding_face = base64.b64encode(face_encoding.tobytes()).decode("utf-8")
        data = {
            "name": name,
            "phone": phone,
            "face_encoding": b64_encoding_face
        }
        res = requests.post(f"{API_BASE}/users/{user_id}", json=data)
        return res.json()
    except Exception as e:
        print(f"[register_user ERROR] {e}")
        return {"status": "error", "message": str(e)}

### 챗봇 대화
def chatbot_reply(session_id: str, user_input: str) -> str:
    """LLM 기반 챗봇 응답"""
    try:
        data = {"session_id": session_id, "user_input": user_input}
        res = requests.post(f"{API_BASE}/chatbot/chat", json=data)
        return res.json().get("reply", "")
    except Exception as e:
        print(f"[chatbot_reply ERROR] {e}")
        return "죄송합니다. 서버 응답에 문제가 있습니다."


### 메뉴 전체 불러오기
def get_all_menus() -> list:
    try:
        res = requests.get(f"{API_BASE}/menu/")
        return res.json()
    except Exception as e:
        print(f"[get_all_menus ERROR] {e}")
        return []


### TTS 
def get_tts_audio(text: str) -> bytes:
    """텍스트를 음성으로 변환하여 음성 바이너리(wav) 반환"""
    try:
        res = requests.post(f"{API_BASE}/tts", json={"text": text})
        if res.status_code == 200:
            return res.content  # .wav 바이트
        else:
            print(f"[TTS Error] {res.status_code}: {res.text}")
            return b""
    except Exception as e:
        print(f"[get_tts_audio ERROR] {e}")
        return b""
