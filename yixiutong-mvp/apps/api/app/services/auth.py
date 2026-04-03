from __future__ import annotations

import base64
from typing import Callable

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel


class PortalUser(BaseModel):
    user_id: str
    username: str
    display_name: str
    role: str
    role_label: str
    department: str
    title: str
    allowed_modules: list[str]


class PortalCredential(BaseModel):
    username: str
    password: str
    profile: PortalUser


_CREDENTIALS: dict[str, PortalCredential] = {
    "zhangwei": PortalCredential(
        username="zhangwei",
        password="123456",
        profile=PortalUser(
            user_id="u-maint-01",
            username="zhangwei",
            display_name="张伟",
            role="maintenance_engineer",
            role_label="维修工程师",
            department="总装运维中心",
            title="维修席位",
            allowed_modules=["dashboard", "fault", "work_orders", "knowledge"],
        ),
    ),
    "liumin": PortalCredential(
        username="liumin",
        password="123456",
        profile=PortalUser(
            user_id="u-proc-01",
            username="liumin",
            display_name="刘敏",
            role="process_engineer",
            role_label="工艺工程师",
            department="工艺技术部",
            title="工艺席位",
            allowed_modules=["dashboard", "process", "approvals", "work_orders", "knowledge"],
        ),
    ),
    "wangyu": PortalCredential(
        username="wangyu",
        password="123456",
        profile=PortalUser(
            user_id="u-quality-01",
            username="wangyu",
            display_name="王钰",
            role="quality_engineer",
            role_label="质量工程师",
            department="质量保证部",
            title="质检席位",
            allowed_modules=["dashboard", "quality", "approvals", "work_orders", "knowledge"],
        ),
    ),
    "chenhao": PortalCredential(
        username="chenhao",
        password="123456",
        profile=PortalUser(
            user_id="u-supervisor-01",
            username="chenhao",
            display_name="陈浩",
            role="supervisor",
            role_label="审批主管",
            department="运行指挥中心",
            title="审批主管",
            allowed_modules=["dashboard", "approvals", "work_orders", "knowledge", "ops", "notifications"],
        ),
    ),
    "admin": PortalCredential(
        username="admin",
        password="123456",
        profile=PortalUser(
            user_id="u-admin-01",
            username="admin",
            display_name="系统管理员",
            role="admin",
            role_label="系统管理员",
            department="数字化平台主管中心",
            title="管理员",
            allowed_modules=["dashboard", "fault", "process", "quality", "approvals", "work_orders", "knowledge", "ops", "notifications"],
        ),
    ),
}

_USERS_BY_ID = {credential.profile.user_id: credential.profile for credential in _CREDENTIALS.values()}


def list_demo_users() -> list[PortalUser]:
    return [credential.profile for credential in _CREDENTIALS.values()]


def authenticate_user(username: str, password: str) -> PortalUser:
    credential = _CREDENTIALS.get(username.strip().lower())
    if credential is None or credential.password != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    return credential.profile


def create_access_token(user: PortalUser) -> str:
    payload = f"yixiutong:{user.user_id}".encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8").rstrip("=")


def resolve_token(token: str) -> PortalUser:
    padding = "=" * (-len(token) % 4)
    try:
        decoded = base64.urlsafe_b64decode(f"{token}{padding}".encode("utf-8")).decode("utf-8")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效登录令牌") from exc
    prefix, _, user_id = decoded.partition(":")
    if prefix != "yixiutong" or not user_id or user_id not in _USERS_BY_ID:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效登录令牌")
    return _USERS_BY_ID[user_id]


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def get_optional_current_user(authorization: str | None = Header(default=None)) -> PortalUser | None:
    token = _extract_bearer_token(authorization)
    if not token:
        return None
    return resolve_token(token)


def get_current_user(authorization: str | None = Header(default=None)) -> PortalUser:
    user = get_optional_current_user(authorization)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    return user


def require_roles(*roles: str) -> Callable[[PortalUser], PortalUser]:
    allowed = set(roles)

    def dependency(user: PortalUser = Depends(get_current_user)) -> PortalUser:
        if user.role not in allowed and user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前角色无权执行该操作")
        return user

    return dependency
