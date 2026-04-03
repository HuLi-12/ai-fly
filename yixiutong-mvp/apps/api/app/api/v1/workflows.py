from __future__ import annotations

from fastapi import APIRouter, Depends

from app.agents.graph import WORKFLOW
from app.models.schemas import ConfirmRequest, ConfirmResponse, DiagnosisRequest, DiagnosisResponse
from app.core.config import get_settings
from app.repositories.portal import PortalRepository
from app.services.auth import PortalUser, get_optional_current_user


router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])


@router.post("/start", response_model=DiagnosisResponse)
def start_diagnosis(request: DiagnosisRequest, user: PortalUser | None = Depends(get_optional_current_user)) -> DiagnosisResponse:
    result = WORKFLOW.invoke({"request": request})
    response = result["response"]
    settings = get_settings()
    portal_repo = PortalRepository(settings.portal_db_path)
    work_order = portal_repo.create_work_order_from_diagnosis(
        request_payload=request.model_dump(),
        diagnosis_response=response.model_dump(),
        user=user,
    )
    response.work_order_id = work_order["work_order_id"]
    return response


@router.post("/confirm", response_model=ConfirmResponse)
def confirm_result(request: ConfirmRequest, user: PortalUser | None = Depends(get_optional_current_user)) -> ConfirmResponse:
    settings = get_settings()
    portal_repo = PortalRepository(settings.portal_db_path)
    work_order = portal_repo.get_work_order_by_request(request.request_id)
    if work_order is not None:
        updated = portal_repo.decide_work_order(
            work_order_id=work_order["work_order_id"],
            approved=request.approved,
            comment=request.operator_note,
            edited_actions=request.edited_actions,
            reviewer=user,
        )
        summary = updated["latest_note"]
    else:
        summary = "人工复核已记录。"
        if request.operator_note:
            summary = f"{summary} 备注：{request.operator_note}"
    return ConfirmResponse(status="confirmed" if request.approved else "rejected", final_summary=summary)
