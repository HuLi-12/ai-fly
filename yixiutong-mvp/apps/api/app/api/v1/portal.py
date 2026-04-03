from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import get_settings
from app.models.schemas import (
    ApprovalDecisionRequest,
    ApprovalTask,
    PortalOverviewResponse,
    PortalSummary,
    UserProfile,
    WorkOrderDetail,
    WorkOrderListItem,
)
from app.repositories.portal import PortalRepository
from app.services.auth import PortalUser, get_current_user


router = APIRouter(prefix="/portal", tags=["portal"])


def _can_view_scene(user: PortalUser, scene_type: str) -> bool:
    if user.role in {"admin", "supervisor"}:
        return True
    if user.role == "maintenance_engineer":
        return scene_type == "fault_diagnosis"
    if user.role == "process_engineer":
        return scene_type == "process_deviation"
    if user.role == "quality_engineer":
        return scene_type == "quality_inspection"
    return False


def _repo() -> PortalRepository:
    settings = get_settings()
    return PortalRepository(settings.portal_db_path)


@router.get("/overview", response_model=PortalOverviewResponse)
def overview(user: PortalUser = Depends(get_current_user)) -> PortalOverviewResponse:
    repo = _repo()
    summary = repo.get_dashboard_summary(user)
    approvals = repo.list_approval_tasks(user)[:6]
    work_orders = repo.list_work_orders(user)[:8]
    return PortalOverviewResponse(
        profile=UserProfile(**user.model_dump()),
        summary=PortalSummary(**summary),
        approvals=[ApprovalTask(**item) for item in approvals],
        work_orders=[WorkOrderListItem(**item) for item in work_orders],
    )


@router.get("/approvals", response_model=list[ApprovalTask])
def approvals(
    include_history: bool = Query(default=False),
    status: str | None = Query(default=None),
    user: PortalUser = Depends(get_current_user),
) -> list[ApprovalTask]:
    repo = _repo()
    return [ApprovalTask(**item) for item in repo.list_approval_tasks(user, include_history=include_history, status=status)]


@router.get("/work-orders", response_model=list[WorkOrderListItem])
def work_orders(
    scene_type: str | None = Query(default=None),
    status_bucket: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    user: PortalUser = Depends(get_current_user),
) -> list[WorkOrderListItem]:
    repo = _repo()
    return [
        WorkOrderListItem(**item)
        for item in repo.list_work_orders(user, scene_type=scene_type, keyword=keyword, status_bucket=status_bucket)
    ]


@router.get("/work-orders/{work_order_id}", response_model=WorkOrderDetail)
def work_order_detail(work_order_id: str, user: PortalUser = Depends(get_current_user)) -> WorkOrderDetail:
    repo = _repo()
    try:
        detail = repo.get_work_order_detail(work_order_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="工单不存在") from exc
    if not _can_view_scene(user, detail["scene_type"]):
        raise HTTPException(status_code=403, detail="无权查看当前工单")
    return WorkOrderDetail(**detail)


@router.post("/work-orders/{work_order_id}/decision", response_model=WorkOrderDetail)
def decide_work_order(
    work_order_id: str,
    request: ApprovalDecisionRequest,
    user: PortalUser = Depends(get_current_user),
) -> WorkOrderDetail:
    repo = _repo()
    try:
        detail = repo.decide_work_order(
            work_order_id=work_order_id,
            approved=request.approved,
            comment=request.comment,
            edited_actions=request.edited_actions,
            reviewer=user,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="工单不存在") from exc
    return WorkOrderDetail(**detail)
