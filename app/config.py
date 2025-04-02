"""
설정 파일
"""

import os

# 프로젝트 루트 디렉토리 경로 (app 폴더의 상위 디렉토리)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 폰트 경로
BOLD_FONT_PATH = os.path.join(ROOT_DIR, "app", "assets", "fonts", "NotoSansKR-Bold.ttf")
LIGHT_FONT_PATH = os.path.join(ROOT_DIR, "app", "assets", "fonts", "NotoSansKR-Light.ttf")

# 이미지 경로
BACK_IMG = os.path.join(ROOT_DIR, "app", "assets", "images", "BG_pattern.png")
LOGO_IMG = os.path.join(ROOT_DIR, "app", "assets", "images", "COMPOSE_LOGO.png")
CHARACTER_IMG = os.path.join(ROOT_DIR, "app", "assets", "images", "V_sample.png")
CARD_IMG = os.path.join(ROOT_DIR, "app", "assets", "images", "Card.png")

# 데이터베이스 경로
DB_PATH = os.path.join(ROOT_DIR, "faces.db")

# 얼굴 인식 설정
FACE_RECOGNITION_TOLERANCE = 0.6
FACE_RECOGNITION_MODEL = "hog"
SIMILARITY_THRESHOLD = 0.45
REQUIRED_FRAMES = 7
MAX_LOST_FRAMES = 2
THRESHOLD = 0.8
TRACKER_MAX_AGE = 90
DELETE_TIMEOUT = 300

# 카메라 설정
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# UI 설정
WINDOW_WIDTH = 540
WINDOW_HEIGHT = 960
WINDOW_TITLE = "4ZO 키오스크"

# 기본 경로 설정
SOURCE_DIR = os.path.join(ROOT_DIR, "Source")

# 윈도우 크기 설정
WINDOW_WIDTH = 540
WINDOW_HEIGHT = 960 