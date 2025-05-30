from fastapi import APIRouter, HTTPException
from app.services.test_service import get_all_users, get_user_by_id

router = APIRouter()


@router.get("/")
def get_data_fake():
    return get_all_users()

@router.get("/{user_id}")
def get_user_fake(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user
