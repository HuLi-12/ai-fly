from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.models.feedback import FeedbackRecord
from app.models.schemas import FeedbackRequest, FeedbackResponse
from app.repositories.feedback import FeedbackRepository
from app.repositories.portal import PortalRepository
from app.services.auth import PortalUser, get_optional_current_user


router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
def save_feedback(request: FeedbackRequest, user: PortalUser | None = Depends(get_optional_current_user)) -> FeedbackResponse:
    settings = get_settings()
    repo = FeedbackRepository(settings.feedback_db_path)
    repo.save(
        FeedbackRecord(
            request_id=request.request_id,
            feedback_type=request.feedback_type,
            feedback_text=request.feedback_text,
            final_resolution=request.final_resolution,
        )
    )
    portal_repo = PortalRepository(settings.portal_db_path)
    work_order = portal_repo.get_work_order_by_request(request.request_id)
    if work_order is not None:
        portal_repo.save_feedback(
            work_order_id=work_order["work_order_id"],
            feedback_text=request.feedback_text,
            final_resolution=request.final_resolution,
            operator=user,
        )
    return FeedbackResponse(saved=True)
