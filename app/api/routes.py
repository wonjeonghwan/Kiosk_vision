"""
API 라우트 정의
"""

from fastapi import APIRouter, HTTPException
from app.models.order import OrderData, OrderItem
from app.models.user import UserData
from app.core.database import Database

router = APIRouter()
db = Database()

@router.post("/orders")
async def create_order(order: OrderData):
    """주문 생성"""
    try:
        # 주문 데이터 저장 로직
        return {"message": "주문이 생성되었습니다", "order_id": 1}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    """사용자 정보 조회"""
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    return user

@router.post("/users")
async def create_user(user: UserData):
    """사용자 생성"""
    try:
        user_id = db.add_user(user)
        return {"message": "사용자가 생성되었습니다", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/menu")
async def get_menu():
    """메뉴 목록 조회"""
    try:
        menu_items = db.get_menu_items()
        return {"menu": menu_items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 