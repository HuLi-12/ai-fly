from __future__ import annotations

import httpx


def _ensure_webhook(channel: dict) -> str:
    webhook_url = (channel.get("webhook_url") or "").strip()
    if not webhook_url:
        raise RuntimeError("Webhook 地址未配置")
    return webhook_url


def _wecom_payload(title: str, content: str) -> dict:
    return {
        "msgtype": "markdown",
        "markdown": {
            "content": f"## {title}\n{content}"
        },
    }


def _feishu_payload(title: str, content: str) -> dict:
    return {
        "msg_type": "text",
        "content": {
            "text": f"{title}\n{content}"
        },
    }


def send_notification(channel: dict, title: str, content: str) -> str:
    webhook_url = _ensure_webhook(channel)
    channel_name = channel["channel"]
    payload = _wecom_payload(title, content) if channel_name == "wecom_bot" else _feishu_payload(title, content)
    response = httpx.post(webhook_url, json=payload, timeout=20.0)
    response.raise_for_status()
    return f"{channel['display_name']} 推送成功"
