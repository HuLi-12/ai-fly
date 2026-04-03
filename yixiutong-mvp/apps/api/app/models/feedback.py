from __future__ import annotations

from pydantic import BaseModel


class FeedbackRecord(BaseModel):
    request_id: str
    feedback_type: str
    feedback_text: str
    final_resolution: str

