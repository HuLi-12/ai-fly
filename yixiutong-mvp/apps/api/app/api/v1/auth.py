from __future__ import annotations

from fastapi import APIRouter, Depends

from app.models.schemas import LoginRequest, LoginResponse, UserProfile
from app.services.auth import authenticate_user, create_access_token, get_current_user, list_demo_users


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
    user = authenticate_user(request.username, request.password)
    return LoginResponse(access_token=create_access_token(user), profile=UserProfile(**user.model_dump()))


@router.get("/me", response_model=UserProfile)
def me(user=Depends(get_current_user)) -> UserProfile:
    return UserProfile(**user.model_dump())


@router.get("/demo-users", response_model=list[UserProfile])
def demo_users() -> list[UserProfile]:
    return [UserProfile(**user.model_dump()) for user in list_demo_users()]
