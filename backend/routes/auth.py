from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from backend.auth import hash_password, verify_password, create_access_token
from backend.database.db import create_user, get_user_by_username, get_user_by_id


router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    if len(request.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username deve ter no minimo 3 caracteres"
        )
    
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha deve ter no minimo 6 caracteres"
        )
    
    password_hash = hash_password(request.password)
    user_id = create_user(request.username, password_hash)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username ja existe"
        )
    
    token = create_access_token(data={"sub": str(user_id), "username": request.username})
    
    return AuthResponse(
        access_token=token,
        user_id=user_id,
        username=request.username
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    user = get_user_by_username(request.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas"
        )
    
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas"
        )
    
    token = create_access_token(data={"sub": str(user["id"]), "username": user["username"]})
    
    return AuthResponse(
        access_token=token,
        user_id=user["id"],
        username=user["username"]
    )


@router.get("/me")
async def get_me(user: dict = Depends(lambda: None)):
    return {"message": "Endpoint de teste"}