from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SceneType = Literal["fault_diagnosis", "process_deviation", "quality_inspection"]


class DiagnosisRequest(BaseModel):
    fault_code: str = Field(min_length=1)
    symptom_text: str = Field(min_length=1)
    device_type: str = Field(default="aviation-equipment")
    context_notes: str = Field(default="")
    scene_type: SceneType = Field(default="fault_diagnosis")


class EvidenceItem(BaseModel):
    source_type: str
    title: str
    snippet: str
    score: float


class DiagnosisResult(BaseModel):
    possible_causes: list[str]
    recommended_checks: list[str]
    recommended_actions: list[str]


class WorkOrderDraft(BaseModel):
    summary: str
    steps: list[str]
    risk_notice: str
    assignee_placeholder: str = "Pending assignment"


class DiagnosisResponse(BaseModel):
    request_id: str
    work_order_id: str = ""
    storage_mode: Literal["workspace-locked"]
    provider_used: str
    scene_type: SceneType
    evidence: list[EvidenceItem]
    diagnosis: DiagnosisResult
    risk_level: Literal["low", "medium", "high"]
    work_order_draft: WorkOrderDraft
    requires_human_confirmation: bool


class ConfirmRequest(BaseModel):
    request_id: str
    approved: bool
    edited_actions: list[str] = Field(default_factory=list)
    operator_note: str = ""


class ConfirmResponse(BaseModel):
    status: Literal["confirmed", "rejected"]
    final_summary: str


class FeedbackRequest(BaseModel):
    request_id: str
    feedback_type: str
    feedback_text: str
    final_resolution: str = ""


class FeedbackResponse(BaseModel):
    saved: bool


class SystemSelfCheck(BaseModel):
    current_free_space_gb: float
    current_project_size_mb: float
    provider: str
    fallback_provider: str
    primary_base_url: str
    fallback_base_url: str
    cache_root: str
    local_model_enabled: bool
    local_model_present: bool
    ollama_executable_path: str
    ollama_executable_present: bool
    controlled_roots: dict[str, str]


class ProviderCheck(BaseModel):
    channel: Literal["primary", "fallback"]
    provider: str
    configured: bool
    reachable: bool
    detail: str


class UserProfile(BaseModel):
    user_id: str
    username: str
    display_name: str
    role: str
    role_label: str
    department: str
    title: str
    allowed_modules: list[str]


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    profile: UserProfile


class PortalSummary(BaseModel):
    work_order_count: int
    pending_approval_count: int
    pending_execution_count: int
    in_progress_count: int
    completed_count: int
    rework_count: int


class PortalOverviewResponse(BaseModel):
    profile: UserProfile
    summary: PortalSummary
    approvals: list["ApprovalTask"]
    work_orders: list["WorkOrderListItem"]


class ApprovalTask(BaseModel):
    approval_id: str
    work_order_id: str
    title: str
    scene_type: SceneType
    scene_label: str
    status: str
    status_label: str
    assignee_role: str
    assignee_name: str
    priority: str
    comment: str
    created_at: str
    updated_at: str


class WorkOrderListItem(BaseModel):
    work_order_id: str
    request_id: str
    title: str
    scene_type: SceneType
    scene_label: str
    status: str
    approval_status: str
    status_bucket: str
    status_bucket_label: str
    priority: str
    risk_level: Literal["low", "medium", "high"]
    applicant_name: str
    applicant_role: str
    assignee_role: str
    assignee_name: str
    summary: str
    symptom_text: str
    provider_used: str
    latest_note: str
    final_resolution: str
    created_at: str
    updated_at: str


class WorkOrderDetail(WorkOrderListItem):
    diagnosis: DiagnosisResult
    evidence: list[EvidenceItem]
    work_order_draft: WorkOrderDraft
    approvals: list[ApprovalTask]


class ApprovalDecisionRequest(BaseModel):
    approved: bool
    comment: str = ""
    edited_actions: list[str] = Field(default_factory=list)


class KnowledgeDocumentSummary(BaseModel):
    document_id: str
    title: str
    category: str
    scene_type: str
    summary: str
    updated_at: str


class KnowledgeDocumentDetail(KnowledgeDocumentSummary):
    content: str
    relative_path: str


class NotificationChannel(BaseModel):
    channel: Literal["wecom_bot", "feishu_bot"]
    display_name: str
    enabled: bool
    webhook_url: str
    secret: str
    receiver_hint: str
    last_status: str
    last_message: str
    updated_at: str


class NotificationChannelUpdateRequest(BaseModel):
    enabled: bool = False
    webhook_url: str = ""
    secret: str = ""
    receiver_hint: str = ""


class NotificationTestRequest(BaseModel):
    title: str = "翼修通消息测试"
    content: str = "这是来自翼修通 OA 门户的测试消息。"


class NotificationTestResponse(BaseModel):
    success: bool
    detail: str


PortalOverviewResponse.model_rebuild()
