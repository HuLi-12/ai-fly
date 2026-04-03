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

export type PortalModule = "dashboard" | "fault" | "process" | "quality" | "approvals" | "work_orders" | "knowledge" | "notifications" | "ops";

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
    deviceType: "复材固化/热处理设备",
    contextNotes: "夹具更换后首批生产，过程记录显示保温时间低于下限。"
  },
  quality_inspection: {
    label: "质量处置",
    faultCode: "QA-305",
    symptomText: "终检发现表面划伤与边缘毛刺，需要立即隔离批次。",
    deviceType: "终检工位",
    contextNotes: "同批次共享同一搬运工位和检验班次，怀疑存在批次性缺陷。"
  }
};

export function useYixiutongWorkspace() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [demoUsers, setDemoUsers] = useState<UserProfile[]>([]);
  const [authLoading, setAuthLoading] = useState(true);
  const [loginLoading, setLoginLoading] = useState(false);

  const [sceneType, setSceneType] = useState<SceneType>("fault_diagnosis");
  const [faultCode, setFaultCode] = useState(scenePresets.fault_diagnosis.faultCode);
  const [symptomText, setSymptomText] = useState(scenePresets.fault_diagnosis.symptomText);
  const [deviceType, setDeviceType] = useState(scenePresets.fault_diagnosis.deviceType);
  const [contextNotes, setContextNotes] = useState(scenePresets.fault_diagnosis.contextNotes);
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

  useEffect(() => {
    void bootstrap();
  }, []);

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
      setError(err instanceof Error ? err.message : "初始化失败");
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
    if (!window.localStorage.getItem("yixiutong-access-token")) {
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

  function applyScenePreset(scene: SceneType = sceneType) {
    const preset = scenePresets[scene];
    setSceneType(scene);
    setFaultCode(preset.faultCode);
    setSymptomText(preset.symptomText);
    setDeviceType(preset.deviceType);
    setContextNotes(preset.contextNotes);
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
      setError(err instanceof Error ? err.message : "登录失败");
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
    setSuccessMessage("已退出当前账号");
  }

  async function openWorkOrder(workOrderId: string) {
    const detail = await fetchWorkOrderDetail(workOrderId);
    setSelectedWorkOrder(detail);
  }

  async function submitDiagnosis() {
    setDiagnosisLoading(true);
    setError("");
    setSuccessMessage("");
    setDecisionMessage("");
    setFeedbackMessage("");
    try {
      const data = await startDiagnosis({
        fault_code: faultCode,
        symptom_text: symptomText,
        device_type: deviceType,
        context_notes: contextNotes,
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
      setError(err instanceof Error ? err.message : "诊断执行失败");
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
      setError(err instanceof Error ? err.message : "审批失败");
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
      setError(err instanceof Error ? err.message : "反馈保存失败");
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
      setError(err instanceof Error ? err.message : "消息配置保存失败");
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
      setError(err instanceof Error ? err.message : "消息测试失败");
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
    setSceneType,
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
    loginAction,
    logoutAction,
    refreshPortalData,
    refreshSystemStatus,
    applyScenePreset,
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
