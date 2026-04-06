from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


SceneType = Literal["fault_diagnosis", "process_deviation", "quality_inspection"]
SupportLevel = Literal["strong", "partial", "weak"]
ProgressStatus = Literal["pending", "running", "completed", "warning", "fallback", "retry", "skipped", "failed"]


class DiagnosisRequest(BaseModel):
    fault_code: str = Field(min_length=1)
    symptom_text: str = Field(min_length=1)
    device_type: str = Field(default="aviation-equipment")
    context_notes: str = Field(default="")
    scene_type: SceneType = Field(default="fault_diagnosis")


class RouteDecision(BaseModel):
    scene_type: SceneType = "fault_diagnosis"
    confidence: float = 0.0
    reason: str = ""
    matched_signals: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    evidence_id: str = ""
    source_type: str
    title: str
    snippet: str
    score: float
    source_path: str = ""
    retrieval_backend: str = ""
    retrieval_method: Literal["keyword", "semantic", "hybrid"] = "semantic"
    keyword_score: float = 0.0
    semantic_score: float = 0.0
    rerank_score: float = 0.0
    model_rerank_score: float = 0.0


class DiagnosisResult(BaseModel):
    possible_causes: list[str]
    recommended_checks: list[str]
    recommended_actions: list[str]


class EvidenceReference(BaseModel):
    evidence_id: str
    title: str
    relevance_score: float
    source_path: str = ""


class TraceabilityItem(BaseModel):
    recommendation: str
    category: Literal["cause", "check", "action"]
    support_score: float
    support_level: SupportLevel
    evidence_links: list[EvidenceReference] = Field(default_factory=list)


class ConfidenceScore(BaseModel):
    overall_score: float = 0.0
    level: Literal["high", "medium", "low"] = "low"
    components: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    requires_human_review: bool = False


class ExecutionTraceItem(BaseModel):
    node: str
    status: Literal["completed", "warning", "fallback", "retry"] = "completed"
    summary: str
    detail: str = ""
    agent: str = ""


class AgentProgressItem(BaseModel):
    node: str
    label: str
    agent: str
    status: ProgressStatus = "pending"
    summary: str = ""
    detail: str = ""
    updated_at: str = ""


class TriggeredRule(BaseModel):
    rule_id: str
    risk_level: Literal["low", "medium", "high"]
    message: str
    matched_keywords: list[str] = Field(default_factory=list)


class WorkOrderStepItem(BaseModel):
    kind: Literal["check", "action"]
    title: str
    instruction: str
    priority: Literal["high", "medium", "low"] = "medium"
    estimated_duration_minutes: int = 15
    action_type: Literal["immediate", "planned", "monitor"] | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    field: str
    severity: Literal["error", "warning"] = "warning"
    message: str
    suggested_fix: str = ""


class ValidationResult(BaseModel):
    status: Literal["ready_to_submit", "needs_revision"] = "ready_to_submit"
    requires_approval: bool = False
    issues: list[ValidationIssue] = Field(default_factory=list)


class WorkOrderDraft(BaseModel):
    summary: str
    steps: list[str]
    risk_notice: str
    assignee_placeholder: str = "Pending assignment"
    scene_type: SceneType = "fault_diagnosis"
    fault_code: str = ""
    symptom_description: str = ""
    evidence_references: list[str] = Field(default_factory=list)
    step_items: list[WorkOrderStepItem] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    approval_required: bool = False
    validation_status: Literal["draft", "ready_to_submit", "needs_revision"] = "draft"


class DiagnosisResponse(BaseModel):
    run_id: str = ""
    request_id: str
    work_order_id: str = ""
    storage_mode: Literal["workspace-locked"]
    provider_used: str
    scene_type: SceneType
    route_confidence: float = 0.0
    route_reason: str = ""
    route_signals: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem]
    diagnosis: DiagnosisResult
    risk_level: Literal["low", "medium", "high"]
    work_order_draft: WorkOrderDraft
    requires_human_confirmation: bool
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    traceability: list[TraceabilityItem] = Field(default_factory=list)
    triggered_rules: list[TriggeredRule] = Field(default_factory=list)
    execution_trace: list[ExecutionTraceItem] = Field(default_factory=list)
    validation_result: ValidationResult = Field(default_factory=ValidationResult)
    approval_reasons: list[str] = Field(default_factory=list)


class DiagnosisSessionStartResponse(BaseModel):
    run_id: str = ""
    session_id: str
    status: Literal["queued", "running", "completed", "failed"] = "queued"


class DiagnosisSessionState(BaseModel):
    run_id: str = ""
    session_id: str
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    current_node: str = ""
    current_agent: str = ""
    started_at: str = ""
    finished_at: str = ""
    error_message: str = ""
    progress: list[AgentProgressItem] = Field(default_factory=list)
    response: DiagnosisResponse | None = None


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
    retrieval_embedding_provider: str = ""
    retrieval_embedding_model: str = ""
    retrieval_vector_enabled: bool = False
    retrieval_model_rerank_enabled: bool = False
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


class AgentRunSnapshot(BaseModel):
    seq: int
    node: str
    status: str
    summary: str
    detail: str = ""
    created_at: str
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentRunReplayResponse(BaseModel):
    run_id: str
    session_id: str = ""
    request_id: str = ""
    request_hash: str
    idempotency_key: str = ""
    status: str
    scene_type: str = ""
    user_id: str = ""
    provider_used: str = ""
    started_at: str
    finished_at: str = ""
    total_duration_ms: float = 0.0
    request: dict[str, Any] = Field(default_factory=dict)
    response: dict[str, Any] = Field(default_factory=dict)
    error_message: str = ""
    snapshots: list[AgentRunSnapshot] = Field(default_factory=list)


class AgentMetricNodeSummary(BaseModel):
    node: str
    count: int
    avg_duration_ms: float
    max_duration_ms: float


class AgentMetricsResponse(BaseModel):
    total_runs: int
    completed_runs: int
    failed_runs: int
    cached_hits: int
    avg_run_duration_ms: float
    node_summaries: list[AgentMetricNodeSummary] = Field(default_factory=list)


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


class LatestTodoItem(BaseModel):
    todo_id: str
    work_order_id: str
    task_type: Literal["approval", "execution", "in_progress", "tracking"]
    title: str
    scene_type: SceneType
    scene_label: str
    status_label: str
    priority: str
    summary: str
    assignee_name: str
    action_label: str
    target_module: Literal["approvals", "work_orders"]
    updated_at: str


class PortalOverviewResponse(BaseModel):
    profile: UserProfile
    summary: PortalSummary
    approvals: list["ApprovalTask"]
    work_orders: list["WorkOrderListItem"]
    latest_todos: list["LatestTodoItem"]


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
    content: str = "这是一条来自翼修通 OA 门户的测试消息。"


class NotificationTestResponse(BaseModel):
    success: bool
    detail: str


PortalOverviewResponse.model_rebuild()
