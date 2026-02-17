import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from auth import create_access_token, get_current_user, hash_password, verify_password
from database import get_db

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(req: RegisterRequest, db=Depends(get_db)):
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = await db.execute_fetchone("SELECT id FROM users WHERE email = ?", [req.email])
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(req.password)
    cursor = await db.execute(
        "INSERT INTO users (email, name, hashed_password) VALUES (?, ?, ?)",
        [req.email, req.name, hashed],
    )
    await db.commit()

    return {"id": cursor.lastrowid, "email": req.email, "name": req.name}


@router.post("/login")
async def login(req: LoginRequest, db=Depends(get_db)):
    row = await db.execute_fetchone("SELECT id, email, name, hashed_password, is_active FROM users WHERE email = ?", [req.email])
    if not row:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = dict(row)
    if not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Account is inactive")

    token = create_access_token({"sub": str(user["id"]), "email": user["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user["id"], "email": user["email"], "name": user["name"]},
    }


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"id": user["id"], "email": user["email"], "name": user["name"]}
