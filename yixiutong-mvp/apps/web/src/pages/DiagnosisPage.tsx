import { AuditBanner } from "../components/AuditBanner";
import { DiagnosisPanel } from "../components/DiagnosisPanel";
import { EvidencePanel } from "../components/EvidencePanel";
import { InputPanel } from "../components/InputPanel";
import { ReviewPanel } from "../components/ReviewPanel";
import { SystemStatusPanel } from "../components/SystemStatusPanel";
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
            onSceneTypeChange={workspace.applyScenePreset}
            onFaultCodeChange={workspace.setFaultCode}
            onSymptomTextChange={workspace.setSymptomText}
            onDeviceTypeChange={workspace.setDeviceType}
            onContextNotesChange={workspace.setContextNotes}
            onSubmit={() => void workspace.submitDiagnosis()}
            onApplyDemoPreset={() => workspace.applyScenePreset()}
            loading={workspace.diagnosisLoading}
          />

          {workspace.result ? (
            <>
              <EvidencePanel evidence={workspace.result.evidence} />
              <DiagnosisPanel diagnosis={workspace.result.diagnosis} riskLevel={workspace.result.risk_level} sceneType={workspace.result.scene_type} />
              <WorkOrderPreview workOrder={workspace.result.work_order_draft} />
            </>
          ) : (
            <section style={panelStyle}>
              <h2 style={{ marginTop: 0 }}>席位说明</h2>
              <p style={{ color: "#5a6d7d", lineHeight: 1.7 }}>
                在这里提交异常后，系统会调用 Agent 做证据召回、结构化建议生成，并自动写入工单中心和待办审批箱。
              </p>
            </section>
          )}
        </div>

        <div style={{ display: "grid", gap: 20, alignContent: "start" }}>
          <SystemStatusPanel selfCheck={workspace.selfCheck} providerChecks={workspace.providerChecks} />

          {workspace.result ? (
            <>
              <AuditBanner requiresHumanConfirmation={workspace.result.requires_human_confirmation} providerUsed={workspace.result.provider_used} />
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
              <h2 style={{ marginTop: 0 }}>流程说明</h2>
              <div style={{ display: "grid", gap: 10 }}>
                {[
                  "提交异常后自动生成工单。",
                  "高风险结果自动进入待办审批箱。",
                  "审批通过后工单流转到执行状态。",
                  "最终处置结果回填后进入工单归档。"
                ].map((item) => (
                  <div key={item} style={infoRowStyle}>{item}</div>
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    </div>
  );
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
  border: "1px solid rgba(9,52,84,0.08)"
} as const;
