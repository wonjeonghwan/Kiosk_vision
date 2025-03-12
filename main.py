import cv2
import numpy as np
from ultralytics import YOLO
from models.face_recognizer import extract_face_embeddings, temporary_encodings
from models.db_manager import save_face, find_best_match
from PIL import ImageFont, ImageDraw, Image

# 한글 폰트 설정 (이름 표시용)
FONT_PATH = "malgun.ttf"

# YOLO 모델 로드
model = YOLO("models/yolov8n.pt")

# 웹캠 열기
cap = cv2.VideoCapture(0)
is_registering = False  # 새로운 사용자 등록 중 상태
new_user_name = ""  # 새로운 사용자 이름

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ 웹캠에서 프레임을 가져올 수 없음.")
        break

    # 얼굴 감지 + 진행률 계산
    encoding, (x1, y1, x2, y2), progress = extract_face_embeddings(frame)

    # 🔹 기본값 설정 (에러 방지)
    user_id = None
    name = ""

    if encoding is not None:
        user_id, name = find_best_match(encoding, threshold=0.45)

        if user_id:  # ✅ 기존 사용자 즉시 인식 (동명이인이라도 ID로 구별됨)
            print(f"✅ 기존 사용자 인식됨: {name}")  
            is_registering = False  # 새로운 사용자 등록 중이었으면 취소
            new_user_name = ""
            temporary_encodings.clear()  # 임시 저장 데이터 삭제
        else:
            if progress >= 100 and not is_registering:  # ✅ 새로운 사용자 30프레임 이상 유지됨
                is_registering = True
                print("🆕 새로운 사용자 발견! 이름을 입력하세요.")
                new_user_name = input("이름 입력: ").strip()

                if new_user_name:
                    save_face(new_user_name, temporary_encodings)  # ✅ 평균 벡터 저장
                    print(f"✅ 신규 사용자 '{new_user_name}' 저장 완료!")
                    temporary_encodings.clear()  # 임시 저장 데이터 삭제
                    is_registering = False  # 등록 완료 후 다시 일반 모드로

    # 얼굴 박스 표시
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # UI 개선: 진행 바 & 상태 메시지 표시
    frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(frame_pil)
    font = ImageFont.truetype(FONT_PATH, 30)

    if is_registering:
        draw.text((x1, y2 + 30), f"🆕 새로운 사용자 '{new_user_name}' 등록 중...", font=font, fill=(255, 0, 0, 255))
    elif user_id:  # 기존 사용자 즉시 이름 표시
        draw.text((x1, y2 + 30), f"✅ {name}", font=font, fill=(0, 255, 0, 255))
    else:  # 새로운 사용자 진행 바 표시
        draw.text((x1, y2 + 30), f"인식 진행: {progress}%", font=font, fill=(0, 255, 0, 255))

    frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)

    # 화면 출력
    cv2.imshow("Face Recognition", frame)

    # 종료 버튼 추가 ('q'를 누르면 종료)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()




# while True:
#     ret, frame = cap.read()
#     if not ret:
#         print("❌ 웹캠에서 프레임을 가져올 수 없음.")
#         break

#     # YOLO로 얼굴 감지
#     results = model(frame)
    
#     detections = []
#     for result in results:
#         for box in result.boxes:
#             if int(box.cls[0]) != 0:  # 0번 클래스가 '사람'임
#                 continue

#             x1, y1, x2, y2 = map(int, box.xyxy[0])
#             detections.append([x1, y1, x2, y2])

#     # 가장 큰 얼굴 하나만 선택 (가장 가까운 사람 기준)
#     if detections:
#         detections.sort(key=lambda box: (box[2] - box[0]) * (box[3] - box[1]), reverse=True)
#         x1, y1, x2, y2 = detections[0]

#         # 얼굴 특징 벡터 추출
#         encoding = extract_face_embeddings(frame, (x1, y1, x2, y2))

#         if encoding is not None:
#             user_id, name = find_best_match(encoding, threshold=0.45)

#             if user_id:
#                 print(f"✅ 기존 사용자 인식됨: {name}")
#             else:
#                 print("🆕 새로운 사용자 발견! 이름을 입력하세요.")
#                 new_name = input("이름 입력: ").strip()

#                 if new_name:
#                     save_face(new_name, encoding)
#                     print(f"✅ 신규 사용자 '{new_name}' 저장 완료!")
#                     name = new_name  # 바로 인식된 이름으로 표시

#             # 얼굴 위에 이름 표시
#             frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
#             draw = ImageDraw.Draw(frame_pil)
#             font = ImageFont.truetype(FONT_PATH, 30)
#             draw.text((x1, y1 - 40), name, font=font, fill=(0, 255, 0, 255))
#             frame = cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)

#         # 얼굴 박스 표시
#         cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

#     cv2.imshow("Face Recognition", frame)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()
