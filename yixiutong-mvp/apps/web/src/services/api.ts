export type SceneType = "fault_diagnosis" | "process_deviation" | "quality_inspection";

export type UserProfile = {
  user_id: string;
  username: string;
  display_name: string;
  role: string;
  role_label: string;
  department: string;
  title: string;
  allowed_modules: string[];
};

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  profile: UserProfile;
};

export type DiagnosisPayload = {
  fault_code: string;
  symptom_text: string;
  device_type: string;
  context_notes: string;
  scene_type: SceneType;
};

export type DiagnosisResponse = {
  request_id: string;
  work_order_id: string;
  storage_mode: "workspace-locked";
  provider_used: string;
  scene_type: SceneType;
  route_confidence: number;
  route_reason: string;
  route_signals: string[];
  evidence: Array<{
    evidence_id: string;
    source_type: string;
    title: string;
    snippet: string;
    score: number;
    source_path?: string;
    retrieval_backend?: string;
    retrieval_method?: "keyword" | "semantic" | "hybrid";
    keyword_score?: number;
    semantic_score?: number;
    rerank_score?: number;
    model_rerank_score?: number;
  }>;
  diagnosis: {
    possible_causes: string[];
    recommended_checks: string[];
    recommended_actions: string[];
  };
  risk_level: "low" | "medium" | "high";
  work_order_draft: {
    summary: string;
    steps: string[];
    risk_notice: string;
    assignee_placeholder: string;
    scene_type?: SceneType;
    fault_code?: string;
    symptom_description?: string;
    evidence_references?: string[];
    safety_notes?: string[];
    approval_required?: boolean;
    validation_status?: "draft" | "ready_to_submit" | "needs_revision";
    step_items?: Array<{
      kind: "check" | "action";
      title: string;
      instruction: string;
      priority: "high" | "medium" | "low";
      estimated_duration_minutes: number;
      action_type?: "immediate" | "planned" | "monitor";
      evidence_ids: string[];
    }>;
  };
  requires_human_confirmation: boolean;
  confidence?: {
    overall_score: number;
    level: "high" | "medium" | "low";
    components: Record<string, number>;
    warnings: string[];
    requires_human_review: boolean;
  };
  traceability?: Array<{
    recommendation: string;
    category: "cause" | "check" | "action";
    support_score: number;
    support_level: "strong" | "partial" | "weak";
    evidence_links: Array<{
      evidence_id: string;
      title: string;
      relevance_score: number;
      source_path?: string;
    }>;
  }>;
  triggered_rules?: Array<{
    rule_id: string;
    risk_level: "low" | "medium" | "high";
    message: string;
    matched_keywords: string[];
  }>;
  execution_trace?: Array<{
    node: string;
    status: "completed" | "warning" | "fallback" | "retry" | "skipped";
    summary: string;
    detail: string;
    agent?: string;
  }>;
  validation_result?: {
    status: "ready_to_submit" | "needs_revision";
    requires_approval: boolean;
    issues: Array<{
      field: string;
      severity: "error" | "warning";
      message: string;
      suggested_fix: string;
    }>;
  };
  approval_reasons?: string[];
};

export type AgentProgressItem = {
  node: string;
  label: string;
  agent: string;
  status: "pending" | "running" | "completed" | "warning" | "fallback" | "retry" | "skipped" | "failed";
  summary: string;
  detail: string;
  updated_at: string;
};

export type DiagnosisSessionStartResponse = {
  session_id: string;
  status: "queued" | "running" | "completed" | "failed";
};

export type DiagnosisSessionState = {
  session_id: string;
  status: "queued" | "running" | "completed" | "failed";
  current_node: string;
  current_agent: string;
  started_at: string;
  finished_at: string;
  error_message: string;
  progress: AgentProgressItem[];
  response?: DiagnosisResponse | null;
};

export type ApprovalTask = {
  approval_id: string;
  work_order_id: string;
  title: string;
  scene_type: SceneType;
  scene_label: string;
  status: string;
  status_label: string;
  assignee_role: string;
  assignee_name: string;
  priority: string;
  comment: string;
  created_at: string;
  updated_at: string;
};

export type WorkOrderListItem = {
  work_order_id: string;
  request_id: string;
  title: string;
  scene_type: SceneType;
  scene_label: string;
  status: string;
  approval_status: string;
  status_bucket: string;
  status_bucket_label: string;
  priority: string;
  risk_level: "low" | "medium" | "high";
  applicant_name: string;
  applicant_role: string;
  assignee_role: string;
  assignee_name: string;
  summary: string;
  symptom_text: string;
  provider_used: string;
  latest_note: string;
  final_resolution: string;
  created_at: string;
  updated_at: string;
};

export type WorkOrderDetail = WorkOrderListItem & {
  diagnosis: DiagnosisResponse["diagnosis"];
  evidence: DiagnosisResponse["evidence"];
  work_order_draft: DiagnosisResponse["work_order_draft"];
  approvals: ApprovalTask[];
};

export type LatestTodoItem = {
  todo_id: string;
  work_order_id: string;
  task_type: "approval" | "execution" | "in_progress" | "tracking";
  title: string;
  scene_type: SceneType;
  scene_label: string;
  status_label: string;
  priority: string;
  summary: string;
  assignee_name: string;
  action_label: string;
  target_module: "approvals" | "work_orders";
  updated_at: string;
};

export type PortalOverviewResponse = {
  profile: UserProfile;
  summary: {
    work_order_count: number;
    pending_approval_count: number;
    pending_execution_count: number;
    in_progress_count: number;
    completed_count: number;
    rework_count: number;
  };
  approvals: ApprovalTask[];
  work_orders: WorkOrderListItem[];
  latest_todos: LatestTodoItem[];
};

export type SelfCheckResponse = {
  provider: string;
  fallback_provider: string;
  retrieval_embedding_provider: string;
  retrieval_embedding_model: string;
  retrieval_vector_enabled: boolean;
  retrieval_model_rerank_enabled: boolean;
  primary_base_url: string;
  fallback_base_url: string;
  cache_root: string;
  local_model_enabled: boolean;
  local_model_present: boolean;
  ollama_executable_path: string;
  ollama_executable_present: boolean;
  controlled_roots: Record<string, string>;
};

export type ProviderCheck = {
  channel: "primary" | "fallback";
  provider: string;
  configured: boolean;
  reachable: boolean;
  detail: string;
};

export type ConfirmPayload = {
  request_id: string;
  approved: boolean;
  edited_actions: string[];
  operator_note: string;
};

export type ConfirmResponse = {
  status: "confirmed" | "rejected";
  final_summary: string;
};

export type FeedbackPayload = {
  request_id: string;
  feedback_type: string;
  feedback_text: string;
  final_resolution: string;
};

export type FeedbackResponse = {
  saved: boolean;
};

export type ApprovalDecisionPayload = {
  approved: boolean;
  comment: string;
  edited_actions: string[];
};

export type KnowledgeDocumentSummary = {
  document_id: string;
  title: string;
  category: string;
  scene_type: string;
  summary: string;
  updated_at: string;
};

export type KnowledgeDocumentDetail = KnowledgeDocumentSummary & {
  content: string;
  relative_path: string;
};

export type NotificationChannel = {
  channel: "wecom_bot" | "feishu_bot";
  display_name: string;
  enabled: boolean;
  webhook_url: string;
  secret: string;
  receiver_hint: string;
  last_status: string;
  last_message: string;
  updated_at: string;
};

export type NotificationTestResponse = {
  success: boolean;
  detail: string;
};

const ACCESS_TOKEN_KEY = "yixiutong-access-token";

function getToken() {
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function persistToken(token: string) {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `请求失败: ${response.status}`;
    try {
      const payload = await response.json();
      if (payload.detail) {
        detail = String(payload.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

async function request<T>(path: string, init?: RequestInit, requireAuth = true): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  if (!headers.has("Content-Type") && init?.body) {
    headers.set("Content-Type", "application/json");
  }
  if (requireAuth) {
    const token = getToken();
    if (!token) {
      throw new Error("请先登录系统。");
    }
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(path, { ...init, headers });
  return readJson<T>(response);
}

export async function login(username: string, password: string) {
  return request<LoginResponse>(
    "/api/v1/auth/login",
    { method: "POST", body: JSON.stringify({ username, password }) },
    false
  );
}

export async function fetchDemoUsers() {
  return request<UserProfile[]>("/api/v1/auth/demo-users", undefined, false);
}

export async function fetchCurrentUser() {
  return request<UserProfile>("/api/v1/auth/me");
}

export async function fetchPortalOverview() {
  return request<PortalOverviewResponse>("/api/v1/portal/overview");
}

export async function fetchApprovals(params?: { include_history?: boolean; status?: string }) {
  const search = new URLSearchParams();
  if (params?.include_history) {
    search.set("include_history", "true");
  }
  if (params?.status) {
    search.set("status", params.status);
  }
  return request<ApprovalTask[]>(`/api/v1/portal/approvals${search.toString() ? `?${search}` : ""}`);
}

export async function fetchWorkOrders(params?: { scene_type?: string; keyword?: string; status_bucket?: string }) {
  const search = new URLSearchParams();
  if (params?.scene_type) {
    search.set("scene_type", params.scene_type);
  }
  if (params?.status_bucket) {
    search.set("status_bucket", params.status_bucket);
  }
  if (params?.keyword) {
    search.set("keyword", params.keyword);
  }
  return request<WorkOrderListItem[]>(`/api/v1/portal/work-orders${search.toString() ? `?${search}` : ""}`);
}

export async function fetchWorkOrderDetail(workOrderId: string) {
  return request<WorkOrderDetail>(`/api/v1/portal/work-orders/${workOrderId}`);
}

export async function decideWorkOrder(workOrderId: string, payload: ApprovalDecisionPayload) {
  return request<WorkOrderDetail>(`/api/v1/portal/work-orders/${workOrderId}/decision`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function startDiagnosis(payload: DiagnosisPayload) {
  return request<DiagnosisResponse>("/api/v1/diagnosis/start", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function startDiagnosisLive(payload: DiagnosisPayload) {
  return request<DiagnosisSessionStartResponse>("/api/v1/diagnosis/start-live", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function fetchDiagnosisSession(sessionId: string) {
  return request<DiagnosisSessionState>(`/api/v1/diagnosis/sessions/${sessionId}`);
}

export async function confirmDiagnosis(payload: ConfirmPayload) {
  return request<ConfirmResponse>("/api/v1/diagnosis/confirm", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function submitFeedback(payload: FeedbackPayload) {
  return request<FeedbackResponse>("/api/v1/feedback", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function fetchSelfCheck() {
  return request<SelfCheckResponse>("/api/v1/system/self-check", undefined, false);
}

export async function fetchProviderChecks() {
  return request<ProviderCheck[]>("/api/v1/system/provider-check", undefined, false);
}

export async function fetchKnowledgeDocuments(params?: { keyword?: string; category?: string }) {
  const search = new URLSearchParams();
  if (params?.keyword) {
    search.set("keyword", params.keyword);
  }
  if (params?.category) {
    search.set("category", params.category);
  }
  return request<KnowledgeDocumentSummary[]>(`/api/v1/knowledge/documents${search.toString() ? `?${search}` : ""}`);
}

export async function fetchKnowledgeDocument(documentId: string) {
  return request<KnowledgeDocumentDetail>(`/api/v1/knowledge/documents/${documentId}`);
}

export async function fetchNotificationChannels() {
  return request<NotificationChannel[]>("/api/v1/notifications/channels");
}

export async function updateNotificationChannel(channel: string, payload: { enabled: boolean; webhook_url: string; secret: string; receiver_hint: string }) {
  return request<NotificationChannel>(`/api/v1/notifications/channels/${channel}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export async function testNotificationChannel(channel: string, payload: { title: string; content: string }) {
  return request<NotificationTestResponse>(`/api/v1/notifications/channels/${channel}/test`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
