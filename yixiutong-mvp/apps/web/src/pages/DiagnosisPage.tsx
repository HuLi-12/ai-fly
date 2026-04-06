import { useEffect } from "react";

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
  useEffect(() => {
    const preset = cleanScenePresets[workspace.sceneType];
    if (looksMojibake(workspace.faultCode)) {
      workspace.setFaultCode(preset.faultCode);
    }
    if (looksMojibake(workspace.symptomText)) {
      workspace.setSymptomText(preset.symptomText);
    }
    if (looksMojibake(workspace.deviceType)) {
      workspace.setDeviceType(preset.deviceType);
    }
    if (looksMojibake(workspace.contextNotes)) {
      workspace.setContextNotes(preset.contextNotes);
    }
  }, [
    workspace.contextNotes,
    workspace.deviceType,
    workspace.faultCode,
    workspace.sceneType,
    workspace.setContextNotes,
    workspace.setDeviceType,
    workspace.setFaultCode,
    workspace.setSymptomText,
    workspace.symptomText,
  ]);

  const guide = buildGuide(workspace);
  const metrics = buildMetrics(workspace);
  const validationErrors = sanitizeValidationErrors(workspace.validationErrors);
  const decisionMessage = sanitizeMessage(workspace.decisionMessage, "审批结果已更新。");
  const feedbackMessage = sanitizeMessage(workspace.feedbackMessage, "反馈已回填，工单状态已刷新。");

  return (
    <div style={pageStyle}>
      <section style={{ ...heroStyle, background: props.moduleTone }}>
        <div style={heroContentStyle}>
          <div>
            <div style={heroEyebrowStyle}>Agent Operation Desk</div>
            <h1 style={{ marginTop: 10, marginBottom: 10 }}>{props.title}</h1>
            <p style={heroDescriptionStyle}>{props.description}</p>
          </div>

          <div style={heroActionsStyle}>
            {(["fault", "process", "quality"] as PortalModule[]).map((module) => (
              <button key={module} type="button" onClick={() => props.onOpenModule(module)} style={moduleButtonStyle}>
                {module === "fault" ? "智能排故" : module === "process" ? "工艺偏差" : "质量处置"}
              </button>
            ))}
          </div>
        </div>

        <div style={metricGridStyle}>
          {metrics.map((item) => (
            <div key={item.label} style={metricCardStyle}>
              <div style={metricLabelStyle}>{item.label}</div>
              <strong style={metricValueStyle}>{item.value}</strong>
              <div style={metricDescStyle}>{item.description}</div>
            </div>
          ))}
        </div>
      </section>

      <WorkflowTracePanel
        session={workspace.diagnosisSession}
        executionTrace={workspace.result?.execution_trace ?? []}
        loading={workspace.diagnosisLoading}
      />

      <SystemStatusPanel selfCheck={workspace.selfCheck} providerChecks={workspace.providerChecks} />

      <div style={mainGridStyle}>
        <div style={{ display: "grid", gap: 18, alignContent: "start" }}>
          <InputPanel
            sceneType={workspace.sceneType}
            faultCode={workspace.faultCode}
            symptomText={workspace.symptomText}
            deviceType={workspace.deviceType}
            contextNotes={workspace.contextNotes}
            validationErrors={validationErrors}
            canSubmit={workspace.canSubmitDiagnosis}
            draftAvailable={workspace.draftAvailable}
            draftSavedAt={workspace.draftSavedAt}
            draftDirty={workspace.draftDirty}
            draftSource={workspace.draftSource}
            onSceneTypeChange={workspace.changeScene}
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

          <section style={guidePanelStyle}>
            <div style={sectionEyebrowStyle}>Operator Guide</div>
            <h2 style={{ marginTop: 8, marginBottom: 12 }}>{guide.title}</h2>
            <div style={{ display: "grid", gap: 10 }}>
              {guide.items.map((item) => (
                <div key={item} style={guideRowStyle}>
                  {item}
                </div>
              ))}
            </div>
          </section>
        </div>

        <div style={{ display: "grid", gap: 18, alignContent: "start" }}>
          {workspace.result ? (
            <>
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
                confirmMessage={decisionMessage}
                feedbackMessage={feedbackMessage}
                onConfirm={async (payload) => {
                  await workspace.decideSelectedWorkOrder({
                    approved: payload.approved,
                    comment: payload.operatorNote,
                    editedActions: payload.editedActions,
                  });
                }}
                onSubmitFeedback={workspace.submitWorkOrderFeedback}
              />
            </>
          ) : (
            <section style={emptyResultStyle}>
              <div style={sectionEyebrowStyle}>Analysis Ready</div>
              <h2 style={{ marginTop: 8, marginBottom: 10 }}>等待分析结果</h2>
              <p style={{ margin: 0, lineHeight: 1.85, color: "#546577" }}>
                提交请求后，系统会先在上方进度条实时展示每个 Agent 正在做什么，以及哪些分支被跳过。完成后，诊断建议、工单草案和审批结果会集中显示在这里。
              </p>
            </section>
          )}
        </div>
      </div>

      {workspace.result ? <EvidencePanel evidence={workspace.result.evidence} /> : null}
    </div>
  );
}

function buildGuide(workspace: WorkspaceController) {
  if (workspace.diagnosisLoading) {
    return {
      title: "分析正在进行",
      items: [
        "上方进度条会持续显示当前由哪个 Agent 正在处理请求，以及二次检索、二次校正、工单修复是否被触发。",
        "分析过程中无需重复提交，系统会自动完成检索、诊断、工单起草和审批判断。",
      ],
    };
  }
  if (workspace.result) {
    return {
      title: "结果已生成",
      items: workspace.result.requires_human_confirmation
        ? ["当前结果需要人工审批，请在右侧闭环区确认或驳回。", "如果现场有修订意见，可以先调整动作建议，再提交审批意见。"]
        : ["当前结果可直接进入执行与反馈阶段。", "如果现场已完成处置，建议立即回填最终结果，让案例沉淀到记忆库中。"],
    };
  }
  return {
    title: "如何提交一条高质量分析请求",
    items: [
      "先选对业务场景，再填写标准编号、设备对象和异常现象。",
      "如果已知班次、批次、环境条件或交接记录，建议写入补充上下文。",
      "提交后系统会先显示 Agent 实时过程，再返回诊断、工单和审批结论。",
    ],
  };
}

function buildMetrics(workspace: WorkspaceController) {
  return [
    {
      label: "Current Agent",
      value: workspace.diagnosisSession?.current_agent || "待启动",
      description: workspace.diagnosisLoading ? "分析正在进行中" : "等待新的分析请求",
    },
    {
      label: "Route Scene",
      value: workspace.result?.scene_type ? sceneDisplay(workspace.result.scene_type) : sceneDisplay(workspace.sceneType),
      description: workspace.result?.route_reason || "系统会自动路由到对应业务场景",
    },
    {
      label: "Decision Gate",
      value: workspace.result?.requires_human_confirmation ? "需要审批" : "自动放行",
      description: workspace.result ? `当前风险等级：${workspace.result.risk_level}` : "依据风险、置信度和工单校验共同决定",
    },
  ];
}

function sceneDisplay(sceneType: string) {
  if (sceneType === "fault_diagnosis") {
    return "智能排故";
  }
  if (sceneType === "process_deviation") {
    return "工艺偏差";
  }
  return "质量处置";
}

function looksMojibake(value: string) {
  return /[�€锛鈥]|鏅鸿兘|璇峰～|宸ヨ壓|璐ㄩ噺|缁堟|鍙戠幇|鎺掓晠/.test(value);
}

function sanitizeMessage(value: string, fallback: string) {
  if (!value) {
    return value;
  }
  return looksMojibake(value) ? fallback : value;
}

function sanitizeValidationErrors(errors: WorkspaceController["validationErrors"]) {
  return {
    faultCode: errors.faultCode ? sanitizeMessage(errors.faultCode, "请填写问题编号或使用当前场景推荐的故障码格式。") : undefined,
    symptomText: errors.symptomText ? sanitizeMessage(errors.symptomText, "请补充异常现象，建议至少描述 8 个字。") : undefined,
    deviceType: errors.deviceType ? sanitizeMessage(errors.deviceType, "请填写设备、工位或产线对象。") : undefined,
  };
}

const cleanScenePresets = {
  fault_diagnosis: {
    faultCode: "E-204",
    symptomText: "设备运行时振动异常，并伴随温度持续升高。",
    deviceType: "航空装配工位",
    contextNotes: "夜班连续运行 6 小时后触发告警升级，需要人工复核后决定是否停机。",
  },
  process_deviation: {
    faultCode: "PROC-118",
    symptomText: "热处理保温时间低于合格窗口，批次参数出现漂移。",
    deviceType: "复材固化 / 热处理设备",
    contextNotes: "夹具更换后首批生产，过程记录显示保温时间低于下限。",
  },
  quality_inspection: {
    faultCode: "QA-305",
    symptomText: "终检发现表面划伤与边缘毛刺，需要立即隔离批次。",
    deviceType: "终检工位",
    contextNotes: "同批次共用同一搬运工位和检验班次，怀疑存在批次性缺陷。",
  },
} as const;

const pageStyle = {
  display: "grid",
  gap: 18,
} as const;

const heroStyle = {
  borderRadius: 32,
  padding: 28,
  color: "#ffffff",
  boxShadow: "0 22px 48px rgba(15, 23, 42, 0.12)",
} as const;

const heroContentStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 18,
  flexWrap: "wrap" as const,
  alignItems: "flex-start",
} as const;

const heroEyebrowStyle = {
  fontSize: 12,
  letterSpacing: 2,
  textTransform: "uppercase" as const,
  opacity: 0.76,
} as const;

const heroDescriptionStyle = {
  margin: 0,
  maxWidth: 860,
  lineHeight: 1.8,
  color: "rgba(255,255,255,0.86)",
} as const;

const heroActionsStyle = {
  display: "flex",
  gap: 10,
  flexWrap: "wrap" as const,
} as const;

const moduleButtonStyle = {
  border: "1px solid rgba(255,255,255,0.16)",
  borderRadius: 999,
  padding: "10px 15px",
  cursor: "pointer",
  fontWeight: 800,
  background: "rgba(255,255,255,0.12)",
  color: "#ffffff",
} as const;

const metricGridStyle = {
  marginTop: 20,
  display: "grid",
  gap: 12,
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
} as const;

const metricCardStyle = {
  borderRadius: 22,
  padding: 16,
  background: "rgba(255,255,255,0.10)",
  border: "1px solid rgba(255,255,255,0.12)",
} as const;

const metricLabelStyle = {
  fontSize: 12,
  letterSpacing: 1.3,
  textTransform: "uppercase" as const,
  opacity: 0.72,
} as const;

const metricValueStyle = {
  display: "block",
  marginTop: 8,
  fontSize: 20,
} as const;

const metricDescStyle = {
  marginTop: 8,
  lineHeight: 1.65,
  opacity: 0.84,
} as const;

const mainGridStyle = {
  display: "grid",
  gap: 18,
  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
  alignItems: "start",
} as const;

const guidePanelStyle = {
  background: "#ffffff",
  border: "1px solid rgba(148, 163, 184, 0.18)",
  borderRadius: 26,
  padding: 22,
  boxShadow: "0 16px 30px rgba(15, 23, 42, 0.05)",
} as const;

const sectionEyebrowStyle = {
  fontSize: 12,
  letterSpacing: 2,
  textTransform: "uppercase" as const,
  color: "#0f4c81",
  fontWeight: 800,
} as const;

const guideRowStyle = {
  padding: 14,
  borderRadius: 16,
  background: "#f8fafc",
  border: "1px solid rgba(148, 163, 184, 0.14)",
  lineHeight: 1.75,
  color: "#243b53",
} as const;

const emptyResultStyle = {
  background: "#ffffff",
  border: "1px dashed rgba(148, 163, 184, 0.28)",
  borderRadius: 26,
  padding: 28,
} as const;
