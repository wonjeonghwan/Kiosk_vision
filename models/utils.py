# models/utils.py

import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image
from models.config import FONT_PATH

# 한글 폰트 로드
def load_korean_font(font_path=FONT_PATH, size=30):
    """
    한글을 출력할 수 있는 폰트를 로드
    :param font_path: 폰트 파일 경로
    :param size: 폰트 크기
    :return: PIL ImageFont 객체
    """
    return ImageFont.truetype(font_path, size)

# 얼굴 박스 및 이름 출력
def draw_face_box(frame, x1, y1, x2, y2, name, saved=True):
    """
    감지된 얼굴 주변에 박스를 그리고, 이름을 표시
    :param frame: 현재 프레임 (OpenCV BGR 이미지)
    :param x1, y1, x2, y2: 얼굴 좌표
    :param name: 인식된 사용자 이름
    :param saved: 기존 등록 사용자(True)인지 신규 사용자(False)인지 여부
    :return: 얼굴 박스를 추가한 프레임
    """
    color = (0, 255, 0, 255) if saved else (255, 165, 0, 255)  # 기존 사용자: 녹색, 신규 사용자: 주황색

    # OpenCV -> PIL 변환
    frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(frame_pil)
    font = load_korean_font()

    # 이름 출력
    draw.text((x1, y1 - 40), name, font=font, fill=color)

    # 얼굴 박스 그리기
    frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0) if saved else (0, 165, 255), 2)

    return frame

# 로그 출력 (디버깅용)
def log_event(message):
    """
    디버깅 및 로그 출력
    :param message: 출력할 메시지
    """
    print(f"[LOG] {message}")
