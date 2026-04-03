from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import get_settings
from app.models.schemas import NotificationChannel, NotificationChannelUpdateRequest, NotificationTestRequest, NotificationTestResponse
from app.repositories.portal import PortalRepository
from app.services.auth import PortalUser, require_roles
from app.services.notifier import send_notification


router = APIRouter(prefix="/notifications", tags=["notifications"])


def _repo() -> PortalRepository:
    settings = get_settings()
    return PortalRepository(settings.portal_db_path)


@router.get("/channels", response_model=list[NotificationChannel])
def channels(user: PortalUser = Depends(require_roles("supervisor", "admin"))) -> list[NotificationChannel]:
    repo = _repo()
    return [NotificationChannel(**{**item, "enabled": bool(item["enabled"])}) for item in repo.list_notification_channels()]


@router.put("/channels/{channel}", response_model=NotificationChannel)
def update_channel(
    channel: str,
    request: NotificationChannelUpdateRequest,
    user: PortalUser = Depends(require_roles("supervisor", "admin")),
) -> NotificationChannel:
    repo = _repo()
    try:
        config = repo.update_notification_channel(
            channel=channel,
            enabled=request.enabled,
            webhook_url=request.webhook_url,
            secret=request.secret,
            receiver_hint=request.receiver_hint,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="消息通道不存在") from exc
    return NotificationChannel(**{**config, "enabled": bool(config["enabled"])})


@router.post("/channels/{channel}/test", response_model=NotificationTestResponse)
def test_channel(
    channel: str,
    request: NotificationTestRequest,
    user: PortalUser = Depends(require_roles("supervisor", "admin")),
) -> NotificationTestResponse:
    repo = _repo()
    try:
        config = repo.get_notification_channel(channel)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="消息通道不存在") from exc

    if not config["enabled"]:
        raise HTTPException(status_code=400, detail="消息通道未启用")
    try:
        detail = send_notification(config, request.title, request.content)
        repo.record_notification_result(channel, "成功", detail)
        return NotificationTestResponse(success=True, detail=detail)
    except Exception as exc:
        repo.record_notification_result(channel, "失败", str(exc))
        raise HTTPException(status_code=400, detail=f"消息发送失败: {exc}") from exc
