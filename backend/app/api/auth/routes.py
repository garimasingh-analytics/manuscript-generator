from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import create_access_token, hash_password, verify_password
from app.db.mongo import users_col
from app.models.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic
from app.utils.ids import str_id
from app.api.auth.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=UserPublic)
async def register(payload: RegisterRequest):
    existing = await users_col().find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    now = datetime.now(tz=timezone.utc).isoformat()
    doc = {
        "email": payload.email.lower(),
        "password_hash": hash_password(payload.password),
        "name": payload.name,
        "created_at": now,
    }
    res = await users_col().insert_one(doc)
    user = {"_id": res.inserted_id, **doc}
    return UserPublic(**str_id(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    user = await users_col().find_one({"email": payload.email.lower()})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(subject=str(user["_id"]))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserPublic)
async def me(current_user: dict = Depends(get_current_user)):
    return UserPublic(**current_user)

