"""
더미 데이터 모듈
"""

class OrderData:
    @staticmethod
    def get_dummy_order_data():
        """더미 주문 데이터 반환"""
        return [
                {"item": "아이스 아메리카노", "price": 5000, "image": "data/menu_images_png/menu_image21.png", "count": 1},
                {"item": "아이스 라떼", "price": 5500, "image": "data/menu_images_png/menu_image24.png", "count": 1},
                {"item": "생딸기주스", "price": 4300, "image": "data/menu_images_png/menu_image17.png", "count": 1},
                {"item": "쫀득카노", "price": 5800, "image": "data/menu_images_png/menu_image1.png", "count": 1}
            ]

class ChatDummy:
    @staticmethod
    def get_chat_sequence():
        """더미 채팅 시퀀스 반환"""
        return [
            {
                "sender": "LLM",
                "text": "안녕하세요! 주문하신 메뉴를 확인해드리겠습니다."
            },
            {
                "sender": "LLM",
                "text": "아메리카노 2잔, 카페라떼 1잔, 카푸치노 1잔을 선택하셨네요."
            },
            {
                "sender": "USER",
                "text": "네, 맞아요."
            },
            {
                "sender": "LLM",
                "text": "총 금액은 19,500원입니다. 결제를 진행하시겠어요?"
            },
            {
                "sender": "USER",
                "text": "네, 결제할게요."
            },
            {
                "sender": "LLM",
                "text": "알겠습니다. 결제 방법을 선택해주세요."
            }
        ] 