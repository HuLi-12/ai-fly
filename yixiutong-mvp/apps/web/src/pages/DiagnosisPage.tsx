import { AuditBanner } from "../components/AuditBanner";
import { DiagnosisPanel } from "../components/DiagnosisPanel";
import { EvidencePanel } from "../components/EvidencePanel";
import { InputPanel } from "../components/InputPanel";
import { ReviewPanel } from "../components/ReviewPanel";
import { SystemStatusPanel } from "../components/SystemStatusPanel";
import { WorkflowTracePanel } from "../components/WorkflowTracePanel";
import { WorkOrderPreview } from "../components/WorkOrderPreview";
import type { PortalModule, WorkspaceController } from "../hooks/useYixiutongWorkspace";

type Props = {
  title: string;
  description: string;
  moduleTone: string;
  workspace: WorkspaceController;
  onOpenModule: (module: PortalModule) => void;
};

export function DiagnosisPage(props: Props) {
  const { workspace } = props;
  const guide = buildGuide(workspace);

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <section
        style={{
          borderRadius: 28,
          padding: 28,
          background: props.moduleTone,
          color: "#fff",
          boxShadow: "0 24px 70px rgba(8, 35, 63, 0.18)"
        }}
      >
        <div style={{ fontSize: 12, letterSpacing: 2, textTransform: "uppercase", opacity: 0.74 }}>业务席位</div>
        <h1 style={{ marginBottom: 10 }}>{props.title}</h1>
        <p style={{ marginBottom: 18, maxWidth: 840, lineHeight: 1.7 }}>{props.description}</p>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {(["fault", "process", "quality"] as PortalModule[]).map((module) => (
            <button
              key={module}
              type="button"
              onClick={() => props.onOpenModule(module)}
              style={{
                border: 0,
                borderRadius: 999,
                padding: "10px 14px",
                cursor: "pointer",
                fontWeight: 700,
                background: "rgba(255,255,255,0.16)",
                color: "#fff"
              }}
            >
              {module === "fault" ? "智能排故" : module === "process" ? "工艺偏差" : "质量处置"}
            </button>
          ))}
        </div>
      </section>

      <div style={{ display: "grid", gap: 20, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))" }}>
        <div style={{ display: "grid", gap: 20 }}>
          <InputPanel
            sceneType={workspace.sceneType}
            faultCode={workspace.faultCode}
            symptomText={workspace.symptomText}
            deviceType={workspace.deviceType}
            contextNotes={workspace.contextNotes}
            validationErrors={workspace.validationErrors}
            canSubmit={workspace.canSubmitDiagnosis}
            draftAvailable={workspace.draftAvailable}
            onSceneTypeChange={workspace.applyScenePreset}
            onFaultCodeChange={workspace.setFaultCode}
            onSymptomTextChange={workspace.setSymptomText}
            onDeviceTypeChange={workspace.setDeviceType}
            onContextNotesChange={workspace.setContextNotes}
            onSubmit={() => void workspace.submitDiagnosis()}
            onApplyDemoPreset={() => workspace.applyScenePreset()}
            onRestoreDraft={() => workspace.restoreDraft()}
            onClearDraft={() => workspace.clearDraftForScene()}
            loading={workspace.diagnosisLoading}
          />

          <section style={panelStyle}>
            <h2 style={{ marginTop: 0 }}>{guide.title}</h2>
            <div style={{ display: "grid", gap: 10 }}>
              {guide.items.map((item) => (
                <div key={item} style={infoRowStyle}>
                  {item}
                </div>
              ))}
            </div>
          </section>

          {workspace.result ? (
            <>
              <WorkflowTracePanel executionTrace={workspace.result.execution_trace ?? []} />
              <EvidencePanel evidence={workspace.result.evidence} />
              <DiagnosisPanel
                diagnosis={workspace.result.diagnosis}
                riskLevel={workspace.result.risk_level}
                sceneType={workspace.result.scene_type}
                confidence={workspace.result.confidence}
                triggeredRules={workspace.result.triggered_rules}
                routeConfidence={workspace.result.route_confidence}
                routeReason={workspace.result.route_reason}
                routeSignals={workspace.result.route_signals}
              />
              <WorkOrderPreview workOrder={workspace.result.work_order_draft} validationResult={workspace.result.validation_result} />
            </>
          ) : null}
        </div>

        <div style={{ display: "grid", gap: 20, alignContent: "start" }}>
          <SystemStatusPanel selfCheck={workspace.selfCheck} providerChecks={workspace.providerChecks} />

          {workspace.result ? (
            <>
              <AuditBanner
                requiresHumanConfirmation={workspace.result.requires_human_confirmation}
                providerUsed={workspace.result.provider_used}
                confidenceScore={workspace.result.confidence?.overall_score}
                approvalReasons={workspace.result.approval_reasons}
              />
              <ReviewPanel
                requestId={workspace.result.request_id}
                workOrderId={workspace.result.work_order_id}
                initialActions={workspace.selectedWorkOrder?.diagnosis.recommended_actions ?? workspace.result.diagnosis.recommended_actions}
                confirmLoading={workspace.decisionLoading}
                feedbackLoading={workspace.feedbackLoading}
                confirmMessage={workspace.decisionMessage}
                feedbackMessage={workspace.feedbackMessage}
                onConfirm={async (payload) => {
                  await workspace.decideSelectedWorkOrder({
                    approved: payload.approved,
                    comment: payload.operatorNote,
                    editedActions: payload.editedActions
                  });
                }}
                onSubmitFeedback={workspace.submitWorkOrderFeedback}
              />
            </>
          ) : (
            <section style={panelStyle}>
              <h2 style={{ marginTop: 0 }}>使用建议</h2>
              <div style={{ display: "grid", gap: 10 }}>
                {[
                  "先确认业务场景，再填写标准编号和异常现象。",
                  "如果本场景有历史草稿，可先恢复后再继续补充。",
                  "提交后系统会自动联动检索、诊断、工单和审批流程。",
                  "高风险结果会自动进入审批闸门，不能直接放行。"
                ].map((item) => (
                  <div key={item} style={infoRowStyle}>
                    {item}
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

function buildGuide(workspace: WorkspaceController) {
  if (workspace.diagnosisLoading) {
    return {
      title: "分析中",
      items: ["系统正在执行路由、检索、诊断和工单起草。", "请等待结果返回，不建议重复点击提交按钮。"]
    };
  }
  if (workspace.result) {
    return {
      title: "下一步建议",
      items: workspace.result.requires_human_confirmation
        ? ["当前结果需要人工审批，请在右侧审批闭环中确认或驳回。", "如需修订动作，可直接编辑后提交审批意见。"]
        : ["当前结果可直接进入执行与反馈环节。", "如现场有补充信息，建议同步回填到反馈闭环。"]
    };
  }
  return {
    title: "流程说明",
    items: [
      "填写故障码、设备对象和异常现象，必要时补充班次与批次信息。",
      "Agent 会自动执行检索、诊断、追溯、评分和工单生成。",
      "结果会根据风险等级和置信度自动决定是否进入审批。"
    ]
  };
}

const panelStyle = {
  background: "rgba(255,255,255,0.92)",
  border: "1px solid rgba(9,52,84,0.1)",
  borderRadius: 24,
  padding: 20,
  boxShadow: "0 18px 40px rgba(20, 37, 55, 0.06)"
} as const;

const infoRowStyle = {
  padding: 14,
  borderRadius: 16,
  background: "#f7fafc",
  border: "1px solid rgba(9,52,84,0.08)",
  lineHeight: 1.7
} as const;
