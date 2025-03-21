# models/config.py

# 얼굴 인식 관련 설정
SIMILARITY_THRESHOLD = 0.45  # 얼굴 유사도 임계값
REQUIRED_FRAMES = 30  # 30프레임 유지 시 이름 입력 요청
DISAPPEAR_FRAMES = 90  # 90프레임(약 3초) 동안 얼굴이 안 보이면 삭제
MAX_LOST_FRAMES = 100 # 얼굴 사라지면 복귀
THRESHOLD = 0.8
# DeepSORT 설정
TRACKER_MAX_AGE = 90  # 트래커가 얼굴을 잃어버린 후 유지할 프레임 수

# 데이터베이스 관련 설정
DELETE_TIMEOUT = 300  # 300프레임 후 DB에서 삭제

# 폰트 설정 (한글 출력을 위해)
FONT_PATH = "malgun.ttf"

DB_PATH = "faces.db"

