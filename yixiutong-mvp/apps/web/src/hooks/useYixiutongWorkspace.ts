import { useEffect, useState } from "react";
import {
  clearToken,
  decideWorkOrder,
  fetchApprovals,
  fetchCurrentUser,
  fetchDemoUsers,
  fetchKnowledgeDocument,
  fetchKnowledgeDocuments,
  fetchNotificationChannels,
  fetchPortalOverview,
  fetchProviderChecks,
  fetchSelfCheck,
  fetchWorkOrderDetail,
  fetchWorkOrders,
  login,
  persistToken,
  startDiagnosis,
  submitFeedback,
  testNotificationChannel,
  updateNotificationChannel,
  type ApprovalTask,
  type DiagnosisResponse,
  type KnowledgeDocumentDetail,
  type KnowledgeDocumentSummary,
  type NotificationChannel,
  type PortalOverviewResponse,
  type ProviderCheck,
  type SceneType,
  type SelfCheckResponse,
  type UserProfile,
  type WorkOrderDetail,
  type WorkOrderListItem
} from "../services/api";

export type PortalModule =
  | "dashboard"
  | "fault"
  | "process"
  | "quality"
  | "approvals"
  | "work_orders"
  | "knowledge"
  | "notifications"
  | "ops";

type DraftPayload = {
  sceneType: SceneType;
  faultCode: string;
  symptomText: string;
  deviceType: string;
  contextNotes: string;
  savedAt: string;
};

type FieldErrors = {
  faultCode?: string;
  symptomText?: string;
  deviceType?: string;
};

const ACCESS_TOKEN_KEY = "yixiutong-access-token";
const DRAFT_STORAGE_PREFIX = "yixiutong-draft:";

const faultCodePatterns: Record<SceneType, RegExp> = {
  fault_diagnosis: /^E-\d{2,4}$/i,
  process_deviation: /^PROC-\d{2,4}$/i,
  quality_inspection: /^QA-\d{2,4}$/i
};

export const scenePresets: Record<
  SceneType,
  { label: string; faultCode: string; symptomText: string; deviceType: string; contextNotes: string }
> = {
  fault_diagnosis: {
    label: "智能排故",
    faultCode: "E-204",
    symptomText: "设备运行时振动异常，并伴随温度持续升高。",
    deviceType: "航空装配工位",
    contextNotes: "夜班连续运行 6 小时后触发告警升级，需要人工复核后决定是否停机。"
  },
  process_deviation: {
    label: "工艺偏差",
    faultCode: "PROC-118",
    symptomText: "热处理保温时间低于合格窗口，批次参数出现漂移。",
    deviceType: "复材固化 / 热处理设备",
    contextNotes: "夹具更换后首批生产，过程记录显示保温时间低于下限。"
  },
  quality_inspection: {
    label: "质量处置",
    faultCode: "QA-305",
    symptomText: "终检发现表面划伤与边缘毛刺，需要立即隔离批次。",
    deviceType: "终检工位",
    contextNotes: "同批次共用同一搬运工位和检验班次，怀疑存在批次性缺陷。"
  }
};

function draftKey(sceneType: SceneType) {
  return `${DRAFT_STORAGE_PREFIX}${sceneType}`;
}

function readDraft(sceneType: SceneType): DraftPayload | null {
  try {
    const raw = window.localStorage.getItem(draftKey(sceneType));
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as DraftPayload;
    if (parsed.sceneType !== sceneType) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function saveDraft(payload: DraftPayload) {
  window.localStorage.setItem(draftKey(payload.sceneType), JSON.stringify(payload));
}

function removeDraft(sceneType: SceneType) {
  window.localStorage.removeItem(draftKey(sceneType));
}

function validateDiagnosisInput(sceneType: SceneType, faultCode: string, symptomText: string, deviceType: string): FieldErrors {
  const errors: FieldErrors = {};
  const normalizedFaultCode = faultCode.trim();
  const normalizedSymptom = symptomText.trim();
  const normalizedDevice = deviceType.trim();

  if (!normalizedFaultCode) {
    errors.faultCode = "请填写问题编号或故障码。";
  } else if (!faultCodePatterns[sceneType].test(normalizedFaultCode)) {
    errors.faultCode = `当前场景建议使用 ${sceneType === "fault_diagnosis" ? "E-204" : sceneType === "process_deviation" ? "PROC-118" : "QA-305"} 这类格式。`;
  }

  if (!normalizedDevice) {
    errors.deviceType = "请填写设备或工位对象。";
  }

  if (!normalizedSymptom) {
    errors.symptomText = "请填写异常现象。";
  } else if (normalizedSymptom.length < 8) {
    errors.symptomText = "异常现象描述过短，建议补充到至少 8 个字。";
  }

  return errors;
}

function humanizeErrorMessage(error: unknown, fallback: string): string {
  const raw = error instanceof Error ? error.message : fallback;
  const lowered = raw.toLowerCase();

  if (lowered.includes("failed to fetch") || lowered.includes("network") || lowered.includes("connection refused")) {
    return "网络连接失败，请检查本地后端、Ollama 或网络后重试。";
  }
  if (lowered.includes("timeout") || lowered.includes("timed out")) {
    return "AI 服务响应超时，请稍后重试；如持续超时，请检查模型服务状态。";
  }
  if (lowered.includes("401") || lowered.includes("403") || lowered.includes("请先登录")) {
    return "登录状态已失效，请重新登录系统。";
  }
  if (lowered.includes("not configured") || lowered.includes("provider") || lowered.includes("base url")) {
    return "模型服务尚未配置完成，请先检查主通道、兜底通道和检索配置。";
  }
  if (lowered.includes("500")) {
    return "系统处理失败，请重试；如持续失败，请检查后端日志。";
  }
  return raw || fallback;
}

export function useYixiutongWorkspace() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [demoUsers, setDemoUsers] = useState<UserProfile[]>([]);
  const [authLoading, setAuthLoading] = useState(true);
  const [loginLoading, setLoginLoading] = useState(false);

  const [sceneType, setSceneTypeState] = useState<SceneType>("fault_diagnosis");
  const [faultCode, setFaultCodeState] = useState(scenePresets.fault_diagnosis.faultCode);
  const [symptomText, setSymptomTextState] = useState(scenePresets.fault_diagnosis.symptomText);
  const [deviceType, setDeviceTypeState] = useState(scenePresets.fault_diagnosis.deviceType);
  const [contextNotes, setContextNotesState] = useState(scenePresets.fault_diagnosis.contextNotes);
  const [draftTouched, setDraftTouched] = useState(false);
  const [draftAvailable, setDraftAvailable] = useState(Boolean(readDraft("fault_diagnosis")));

  const [diagnosisLoading, setDiagnosisLoading] = useState(false);
  const [decisionLoading, setDecisionLoading] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [notificationSaving, setNotificationSaving] = useState(false);

  const [result, setResult] = useState<DiagnosisResponse | null>(null);
  const [overview, setOverview] = useState<PortalOverviewResponse | null>(null);
  const [approvals, setApprovals] = useState<ApprovalTask[]>([]);
  const [workOrders, setWorkOrders] = useState<WorkOrderListItem[]>([]);
  const [selectedWorkOrder, setSelectedWorkOrder] = useState<WorkOrderDetail | null>(null);
  const [knowledgeDocuments, setKnowledgeDocuments] = useState<KnowledgeDocumentSummary[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<KnowledgeDocumentDetail | null>(null);
  const [notificationChannels, setNotificationChannels] = useState<NotificationChannel[]>([]);
  const [selfCheck, setSelfCheck] = useState<SelfCheckResponse | null>(null);
  const [providerChecks, setProviderChecks] = useState<ProviderCheck[]>([]);

  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [decisionMessage, setDecisionMessage] = useState("");
  const [feedbackMessage, setFeedbackMessage] = useState("");

  const validationErrors = validateDiagnosisInput(sceneType, faultCode, symptomText, deviceType);
  const canSubmitDiagnosis = !diagnosisLoading && Object.keys(validationErrors).length === 0;

  useEffect(() => {
    void bootstrap();
  }, []);

  useEffect(() => {
    setDraftAvailable(Boolean(readDraft(sceneType)));
  }, [sceneType]);

  useEffect(() => {
    if (!draftTouched) {
      return;
    }
    saveDraft({
      sceneType,
      faultCode,
      symptomText,
      deviceType,
      contextNotes,
      savedAt: new Date().toISOString()
    });
    setDraftAvailable(true);
  }, [sceneType, faultCode, symptomText, deviceType, contextNotes, draftTouched]);

  async function bootstrap() {
    setAuthLoading(true);
    try {
      const users = await fetchDemoUsers();
      setDemoUsers(users);
      try {
        const profile = await fetchCurrentUser();
        setUser(profile);
        await Promise.all([refreshPortalData(), refreshSystemStatus(), loadKnowledgeDocuments(), loadNotificationChannels(profile)]);
      } catch {
        clearToken();
        setUser(null);
        await refreshSystemStatus();
      }
    } catch (err) {
      setError(humanizeErrorMessage(err, "初始化失败"));
    } finally {
      setAuthLoading(false);
    }
  }

  async function refreshSystemStatus() {
    const [systemData, providerData] = await Promise.all([fetchSelfCheck(), fetchProviderChecks()]);
    setSelfCheck(systemData);
    setProviderChecks(providerData);
  }

  async function refreshPortalData() {
    if (!window.localStorage.getItem(ACCESS_TOKEN_KEY)) {
      return;
    }
    const [overviewData, approvalData, workOrderData] = await Promise.all([
      fetchPortalOverview(),
      fetchApprovals(),
      fetchWorkOrders()
    ]);
    setOverview(overviewData);
    setApprovals(approvalData);
    setWorkOrders(workOrderData);
    if (selectedWorkOrder) {
      const refreshed = await fetchWorkOrderDetail(selectedWorkOrder.work_order_id);
      setSelectedWorkOrder(refreshed);
    }
  }

  async function loadKnowledgeDocuments(params?: { keyword?: string; category?: string }) {
    const documents = await fetchKnowledgeDocuments(params);
    setKnowledgeDocuments(documents);
    if (documents.length === 0) {
      setSelectedDocument(null);
      return;
    }

    const currentDocumentId = selectedDocument?.document_id;
    const nextDocumentId =
      params || !currentDocumentId || !documents.some((item) => item.document_id === currentDocumentId)
        ? documents[0].document_id
        : currentDocumentId;

    if (nextDocumentId !== currentDocumentId) {
      const detail = await fetchKnowledgeDocument(nextDocumentId);
      setSelectedDocument(detail);
      return;
    }

    if (!selectedDocument) {
      const detail = await fetchKnowledgeDocument(documents[0].document_id);
      setSelectedDocument(detail);
    }
  }

  async function openDocument(documentId: string) {
    const detail = await fetchKnowledgeDocument(documentId);
    setSelectedDocument(detail);
  }

  async function loadNotificationChannels(profile: UserProfile | null = user) {
    if (!profile || !profile.allowed_modules.includes("notifications")) {
      setNotificationChannels([]);
      return;
    }
    const channels = await fetchNotificationChannels();
    setNotificationChannels(channels);
  }

  function clearTransientMessages() {
    setError("");
    setSuccessMessage("");
    setDecisionMessage("");
    setFeedbackMessage("");
  }

  function applyScenePreset(scene: SceneType = sceneType) {
    const preset = scenePresets[scene];
    setSceneTypeState(scene);
    setFaultCodeState(preset.faultCode);
    setSymptomTextState(preset.symptomText);
    setDeviceTypeState(preset.deviceType);
    setContextNotesState(preset.contextNotes);
    setDraftTouched(false);
    setResult(null);
    setSelectedWorkOrder(null);
    clearTransientMessages();
    setDraftAvailable(Boolean(readDraft(scene)));
  }

  function restoreDraft(scene: SceneType = sceneType) {
    const draft = readDraft(scene);
    if (!draft) {
      setError("当前场景没有可恢复的草稿。");
      return;
    }
    setSceneTypeState(scene);
    setFaultCodeState(draft.faultCode);
    setSymptomTextState(draft.symptomText);
    setDeviceTypeState(draft.deviceType);
    setContextNotesState(draft.contextNotes);
    setDraftTouched(true);
    setResult(null);
    setSelectedWorkOrder(null);
    clearTransientMessages();
    setSuccessMessage(`已恢复 ${scenePresets[scene].label} 草稿。`);
    setDraftAvailable(true);
  }

  function clearDraftForScene(scene: SceneType = sceneType) {
    removeDraft(scene);
    if (scene === sceneType) {
      setDraftAvailable(false);
      setSuccessMessage(`已清除 ${scenePresets[scene].label} 草稿。`);
    }
  }

  function setFaultCode(value: string) {
    setFaultCodeState(value);
    setDraftTouched(true);
  }

  function setSymptomText(value: string) {
    setSymptomTextState(value);
    setDraftTouched(true);
  }

  function setDeviceType(value: string) {
    setDeviceTypeState(value);
    setDraftTouched(true);
  }

  function setContextNotes(value: string) {
    setContextNotesState(value);
    setDraftTouched(true);
  }

  async function loginAction(username: string, password: string) {
    setLoginLoading(true);
    setError("");
    try {
      const response = await login(username, password);
      persistToken(response.access_token);
      setUser(response.profile);
      setSuccessMessage(`欢迎回来，${response.profile.display_name}`);
      setDecisionMessage("");
      setFeedbackMessage("");
      await Promise.all([
        refreshSystemStatus(),
        (async () => {
          const [overviewData, approvalData, workOrderData, docs] = await Promise.all([
            fetchPortalOverview(),
            fetchApprovals(),
            fetchWorkOrders(),
            fetchKnowledgeDocuments()
          ]);
          setOverview(overviewData);
          setApprovals(approvalData);
          setWorkOrders(workOrderData);
          setKnowledgeDocuments(docs);
          if (docs.length > 0) {
            const detail = await fetchKnowledgeDocument(docs[0].document_id);
            setSelectedDocument(detail);
          }
        })(),
        loadNotificationChannels(response.profile)
      ]);
    } catch (err) {
      setError(humanizeErrorMessage(err, "登录失败"));
      throw err;
    } finally {
      setLoginLoading(false);
    }
  }

  function logoutAction() {
    clearToken();
    setUser(null);
    setOverview(null);
    setApprovals([]);
    setWorkOrders([]);
    setSelectedWorkOrder(null);
    setSelectedDocument(null);
    setResult(null);
    setNotificationChannels([]);
    setSuccessMessage("已退出当前账号。");
  }

  async function openWorkOrder(workOrderId: string) {
    const detail = await fetchWorkOrderDetail(workOrderId);
    setSelectedWorkOrder(detail);
  }

  async function submitDiagnosis() {
    if (!canSubmitDiagnosis) {
      const firstError = validationErrors.faultCode ?? validationErrors.deviceType ?? validationErrors.symptomText ?? "请先补齐输入信息。";
      setError(firstError);
      return;
    }

    setDiagnosisLoading(true);
    clearTransientMessages();
    try {
      const data = await startDiagnosis({
        fault_code: faultCode.trim(),
        symptom_text: symptomText.trim(),
        device_type: deviceType.trim(),
        context_notes: contextNotes.trim(),
        scene_type: sceneType
      });
      setResult(data);
      if (data.work_order_id) {
        const detail = await fetchWorkOrderDetail(data.work_order_id);
        setSelectedWorkOrder(detail);
      }
      await Promise.all([refreshPortalData(), refreshSystemStatus()]);
      setSuccessMessage("Agent 已完成分析，并生成工单与审批流。");
    } catch (err) {
      setError(humanizeErrorMessage(err, "诊断执行失败"));
    } finally {
      setDiagnosisLoading(false);
    }
  }

  async function decideSelectedWorkOrder(payload: { approved: boolean; comment: string; editedActions: string[] }) {
    if (!selectedWorkOrder && !result?.work_order_id) {
      return;
    }
    const workOrderId = selectedWorkOrder?.work_order_id ?? result?.work_order_id ?? "";
    setDecisionLoading(true);
    setError("");
    setDecisionMessage("");
    try {
      const detail = await decideWorkOrder(workOrderId, {
        approved: payload.approved,
        comment: payload.comment,
        edited_actions: payload.editedActions
      });
      setSelectedWorkOrder(detail);
      await refreshPortalData();
      setDecisionMessage(payload.approved ? "审批已通过，工单已流转到执行状态。" : "审批已驳回，工单回到重审状态。");
    } catch (err) {
      setError(humanizeErrorMessage(err, "审批失败"));
    } finally {
      setDecisionLoading(false);
    }
  }

  async function submitWorkOrderFeedback(payload: { feedbackType: string; feedbackText: string; finalResolution: string }) {
    const requestId = selectedWorkOrder?.request_id ?? result?.request_id;
    if (!requestId) {
      return;
    }
    setFeedbackLoading(true);
    setError("");
    setFeedbackMessage("");
    try {
      await submitFeedback({
        request_id: requestId,
        feedback_type: payload.feedbackType,
        feedback_text: payload.feedbackText,
        final_resolution: payload.finalResolution
      });
      await refreshPortalData();
      if (selectedWorkOrder) {
        const detail = await fetchWorkOrderDetail(selectedWorkOrder.work_order_id);
        setSelectedWorkOrder(detail);
      }
      setFeedbackMessage("反馈已回填，工单状态已刷新。");
    } catch (err) {
      setError(humanizeErrorMessage(err, "反馈保存失败"));
    } finally {
      setFeedbackLoading(false);
    }
  }

  async function saveNotificationChannel(channel: string, payload: { enabled: boolean; webhook_url: string; secret: string; receiver_hint: string }) {
    setNotificationSaving(true);
    setError("");
    try {
      const updated = await updateNotificationChannel(channel, payload);
      setNotificationChannels((current) => current.map((item) => (item.channel === channel ? updated : item)));
      setSuccessMessage("消息通道配置已保存。");
    } catch (err) {
      setError(humanizeErrorMessage(err, "消息配置保存失败"));
    } finally {
      setNotificationSaving(false);
    }
  }

  async function runNotificationTest(channel: string, payload: { title: string; content: string }) {
    setNotificationSaving(true);
    setError("");
    try {
      const response = await testNotificationChannel(channel, payload);
      await loadNotificationChannels();
      setSuccessMessage(response.detail);
    } catch (err) {
      setError(humanizeErrorMessage(err, "消息测试失败"));
    } finally {
      setNotificationSaving(false);
    }
  }

  return {
    user,
    demoUsers,
    authLoading,
    loginLoading,
    sceneType,
    faultCode,
    symptomText,
    deviceType,
    contextNotes,
    setSceneType: setSceneTypeState,
    setFaultCode,
    setSymptomText,
    setDeviceType,
    setContextNotes,
    diagnosisLoading,
    decisionLoading,
    feedbackLoading,
    notificationSaving,
    result,
    overview,
    approvals,
    workOrders,
    selectedWorkOrder,
    knowledgeDocuments,
    selectedDocument,
    notificationChannels,
    selfCheck,
    providerChecks,
    error,
    successMessage,
    decisionMessage,
    feedbackMessage,
    scenePresets,
    validationErrors,
    canSubmitDiagnosis,
    draftAvailable,
    loginAction,
    logoutAction,
    refreshPortalData,
    refreshSystemStatus,
    applyScenePreset,
    restoreDraft,
    clearDraftForScene,
    submitDiagnosis,
    openWorkOrder,
    decideSelectedWorkOrder,
    submitWorkOrderFeedback,
    loadKnowledgeDocuments,
    openDocument,
    saveNotificationChannel,
    runNotificationTest,
    loadNotificationChannels,
    setSuccessMessage,
    setError
  };
}

export type WorkspaceController = ReturnType<typeof useYixiutongWorkspace>;
