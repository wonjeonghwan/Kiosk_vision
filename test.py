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