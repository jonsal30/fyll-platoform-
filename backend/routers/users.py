from fastapi import APIRouter, Header, HTTPException, Depends
from typing import Optional, List
from backend import services
from backend import schemas
from backend.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=List[schemas.UserOut])
async def list_users(limit: int = 100):
    users = services.list_users(limit=limit)
    return users


@router.get("/{user_id}", response_model=schemas.UserOut)
async def get_user(user_id: str):
    user = services.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user


@router.post("/", status_code=201, response_model=schemas.UserOut)
async def create_user(payload: schemas.UserCreate, idempotency_key: Optional[str] = Header(None)):
    # Create user (idempotency via header)
    created = services.create_user(payload.dict(), idempotency_key=idempotency_key)
    return created


@router.patch("/{user_id}", response_model=schemas.UserOut)
async def patch_user(user_id: str, payload: schemas.UserUpdate, current_user=Depends(get_current_user)):
    user = services.update_user(user_id, payload.dict())
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: str, current_user=Depends(get_current_user)):
    deleted = services.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="user not found")
    return {}
