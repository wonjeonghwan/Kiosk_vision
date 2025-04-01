import requests

def send_to_server(user_text: str):
    url = "http://192.168.10.70:8080/chatbot/chat"
    payload = {
        "session_id": "kiosk-session-001",  # 추후 변경 
        "user_input": user_text
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"서버 오류: {response.status_code}")
            print("서버 응답:", response.text)
            return None
    except Exception as e:
        print(f"서버 통신 실패: {e}")
        return None


