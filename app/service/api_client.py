"""
FastAPI 서버와 통신 
"""

import requests
import base64
import threading
import numpy as np
import hashlib
import json

API_BASE = "http://192.168.20.109:8080"
session_lock = threading.Lock()  # 전역 락 추가

def _encode_session_id(session_id):
    """세션 ID를 안전하게 인코딩"""
    try:
        if isinstance(session_id, np.ndarray):
            # numpy 배열의 해시값을 사용
            # 배열의 처음 10개 값만 사용하여 해시 생성
            hash_input = str(session_id[:10].tolist()).encode('utf-8')
            hash_value = hashlib.md5(hash_input).hexdigest()
            return hash_value
        elif isinstance(session_id, bytes):
            return base64.b64encode(session_id).decode('utf-8')
        elif isinstance(session_id, str):
            return base64.b64encode(session_id.encode('utf-8')).decode('utf-8')
        else:
            return base64.b64encode(str(session_id).encode('utf-8')).decode('utf-8')
    except Exception as e:
        print(f"[_encode_session_id ERROR] {e}")
        return ""

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

### TODO : 세션 아이디 
### 챗봇 세션 초기화 
def chatbot_session_init(session_id: str) -> str : 
    """ 챗봇 시작 전 세션 초기화 """
    try: 
        b64_encoding_id = _encode_session_id(session_id)
        res = requests.get(f"{API_BASE}/chatbot/initialize-session?session_id={b64_encoding_id}")
        return res.json().get("reply", "")
    except Exception as e:
        print(f"[chatbot_session_init ERROR] {e}")
        return "죄송합니다. 서버 응답에 문제가 있습니다."

### 챗봇 대화
def chatbot_reply(session_id: str, user_input: str) -> str:
    """LLM 기반 챗봇 응답"""
    print("🤖 chatbot_reply 시작")
    print("text : ", user_input)
    with session_lock:
        print("🔒 session_lock 획득")
        try:
            print(f"🔍 세션 ID 타입: {type(session_id)}")
            # numpy 배열인 경우 해시값으로 변환
            if isinstance(session_id, np.ndarray):
                hash_input = str(session_id[:10].tolist()).encode('utf-8')
                session_id = hashlib.md5(hash_input).hexdigest()
                print("🔧 numpy 배열을 해시값으로 변환")
                
            b64_encoding_id = _encode_session_id(session_id)
            if not b64_encoding_id:
                print("❌ 세션 ID 인코딩 실패")
                return "죄송합니다. 세션 ID 처리에 문제가 발생했습니다."
                
            print("📤 API 요청 전송")
            data = {"session_id": b64_encoding_id, "user_input": user_input}
            print("data : ", data)
            
            # 타임아웃 설정 추가
            try:
                print(f"🌐 서버 URL: {API_BASE}/chatbot/chat")
                print("🔄 API 요청 시도 중...")
                
                res = requests.post(
                    f"{API_BASE}/chatbot/chat", 
                    json=data,
                    timeout=10,
                    headers={'Content-Type': 'application/json'}
                )
                
                print(f"📥 응답 status: {res.status_code}")
                print(f"📥 응답 headers: {res.headers}")
                print(f"📥 응답 content: {res.content[:200]}")  # 처음 200바이트만 출력
                print(f"📥 응답 text: {res.text[:200]}")  # 처음 200자만 출력
                
                if res.status_code != 200:
                    print(f"❌ 서버 오류: {res.status_code}")
                    return "죄송합니다. 서버에서 오류가 발생했습니다."
                
                # 응답이 진짜 JSON인지 확인
                if res.headers.get("content-type", "").startswith("application/json"):
                    response_data = res.json()
                    if "response" in response_data:
                        response = response_data["response"]
                        print(f"📥 API 응답 수신: {response[:50]}...")
                        return response
                    else:
                        print("❌ 잘못된 응답 형식:", response_data)
                        return "죄송합니다. 서버 응답 형식에 문제가 있습니다."
                else:
                    print("❌ 응답이 JSON이 아님")
                    return "서버 응답 형식 오류입니다."
                    
            except requests.exceptions.Timeout:
                print("⏰ API 요청 시간 초과")
                return "죄송합니다. 서버 응답이 지연되고 있습니다."
            except requests.exceptions.RequestException as e:
                print(f"❌ API 요청 실패: {str(e)}")
                return "죄송합니다. 서버와의 통신에 문제가 발생했습니다."
            except json.JSONDecodeError as e:
                print(f"❌ JSON 파싱 오류: {str(e)}")
                return "죄송합니다. 서버 응답을 처리하는 중 문제가 발생했습니다."
                
        except Exception as e:
            print(f"❌ chatbot_reply 오류: {str(e)}")
            return "죄송합니다. 다시 말씀해 주세요."
        finally:
            print("�� session_lock 해제")

### 챗봇 세션 저장 
def chatbot_session_save(session_id: str) -> str:
    """현재 세션의 대화 내용을 벡터 DB에 저장"""
    with session_lock:
        try:
            b64_encoding_id = _encode_session_id(session_id)
            if not b64_encoding_id:
                return "죄송합니다. 세션 ID 처리에 문제가 발생했습니다."
                
            data = {"session_id": b64_encoding_id}
            res = requests.post(f"{API_BASE}/chatbot/save-session", json=data)
            return res.json().get("reply", "")
        except Exception as e:
            print(f"[chatbot_session_save ERROR] {e}")
            return "죄송합니다. 서버 응답에 문제가 있습니다."
    
### 챗봇 세션(버퍼) 클리어 
def chatbot_session_clear(session_id: str) -> str:
    """챗봇 세션 내 대화 이력 초기화 및 삭제"""
    with session_lock:
        try:
            b64_encoding_id = _encode_session_id(session_id)
            if not b64_encoding_id:
                return "죄송합니다. 세션 ID 처리에 문제가 발생했습니다."
                
            res = requests.delete(f"{API_BASE}/chatbot/clear-session?session_id={b64_encoding_id}")
            return res.json().get("reply", "")
        except Exception as e:
            print(f"[chatbot_session_clear ERROR] {e}")
            return "죄송합니다. 서버 응답에 문제가 있습니다."

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
    
### 메뉴 전체 불러오기
def get_all_menus() -> list:
    try:
        res = requests.get(f"{API_BASE}/menu/")
        return res.json()
    except Exception as e:
        print(f"[get_all_menus ERROR] {e}")
        return []