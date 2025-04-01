"""
설정 파일
"""

import os

# 기본 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 폰트 경로
BOLD_FONT_PATH = os.path.join(BASE_DIR, "Source", "NotoSansKR-Bold.ttf")
LIGHT_FONT_PATH = os.path.join(BASE_DIR, "Source", "NotoSansKR-Light.ttf")

# 이미지 경로
BACK_IMG = os.path.join(BASE_DIR, "Source", "BG_pattern.png")
LOGO_IMG = os.path.join(BASE_DIR, "Source", "COMPOSE_LOGO.png")
CHARACTER_IMG = os.path.join(BASE_DIR, "Source", "V_sample.png")
CARD_IMG = os.path.join(BASE_DIR, "Source", "Card.png")

# 데이터베이스 경로
DB_PATH = os.path.join(BASE_DIR, "data", "kiosk.db")

# 얼굴 인식 설정
FACE_RECOGNITION_TOLERANCE = 0.6
FACE_RECOGNITION_MODEL = "hog"

# 카메라 설정
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# UI 설정
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
WINDOW_TITLE = "4ZO 키오스크"

# 기본 경로 설정
SOURCE_DIR = os.path.join(BASE_DIR, "Source")

# 폰트 경로
SIMILARITY_THRESHOLD = 0.45
REQUIRED_FRAMES = 7
MAX_LOST_FRAMES = 2
THRESHOLD = 0.8
TRACKER_MAX_AGE = 90
DELETE_TIMEOUT = 300

# 윈도우 크기 설정
WINDOW_WIDTH = 540
WINDOW_HEIGHT = 960 