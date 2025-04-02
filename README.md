# 4ZO 키오스크

## 프로젝트 구조
```
4ZO/
├── app/
│   ├── assets/
│   │   ├── fonts/
│   │   │   ├── NotoSansKR-Bold.ttf
│   │   │   ├── NotoSansKR-Light.ttf
│   │   │   └── NotoSansKR-Medium.ttf
│   │   └── images/
│   │       ├── background.png
│   │       ├── logo.png
│   │       ├── character.png
│   │       └── card.png
│   ├── core/
│   │   └── face_detection.py
│   ├── gui/
│   │   ├── screens/
│   │   │   ├── base_screen.py
│   │   │   ├── waiting_screen.py
│   │   │   ├── new_user_screen.py
│   │   │   ├── order_screen.py
│   │   │   ├── order_issuance_screen.py
│   │   │   └── payment_screen.py
│   │   └── widgets/
│   │       └── touch_keyboard.py
│   ├── config.py
│   └── __init__.py
├── faces.db
└── run.py
```

## 실행 방법
1. 프로젝트를 클론합니다:
```bash
git clone [repository-url]
cd 4ZO
```

2. 필요한 패키지를 설치합니다:
```bash
pip install -r requirements.txt
```

3. 프로젝트 루트 디렉토리에서 실행합니다:
```bash
python run.py
```

## 주의사항
- 프로젝트는 반드시 루트 디렉토리(`4ZO/`)에서 실행해야 합니다.
- 모든 자산 파일(폰트, 이미지)은 지정된 경로에 있어야 합니다.
- 데이터베이스 파일(`faces.db`)은 자동으로 생성됩니다. 