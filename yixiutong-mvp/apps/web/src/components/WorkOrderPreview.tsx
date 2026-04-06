import { CollapsibleSection } from "./CollapsibleSection";

type StepItem = {
  kind: "check" | "action";
  title?: string;
  instruction: string;
  priority: "high" | "medium" | "low";
  estimated_duration_minutes: number;
  action_type?: "immediate" | "planned" | "monitor";
};

type ValidationResult = {
  status: "ready_to_submit" | "needs_revision";
  requires_approval: boolean;
  issues: Array<{
    field: string;
    severity: "error" | "warning";
    message: string;
    suggested_fix: string;
  }>;
};

type WorkOrderDraft = {
  summary: string;
  steps: string[];
  risk_notice: string;
  assignee_placeholder: string;
  evidence_references?: string[];
  safety_notes?: string[];
  approval_required?: boolean;
  step_items?: StepItem[];
};

const priorityLabel = {
  high: "高",
  medium: "中",
  low: "低",
} as const;

const actionTypeLabel = {
  immediate: "立即执行",
  planned: "计划执行",
  monitor: "持续观察",
} as const;

export function WorkOrderPreview(props: { workOrder: WorkOrderDraft; validationResult?: ValidationResult }) {
  const stepItems = props.workOrder.step_items ?? [];
  const badge =
    props.validationResult?.status === "needs_revision"
      ? "待修订"
      : props.validationResult?.status === "ready_to_submit"
        ? "可提交"
        : "草稿";

  return (
    <CollapsibleSection
      title="工单草案"
      subtitle="工单会先给出结构化步骤，再说明审批要求、安全注意事项和校验结果。"
      badge={badge}
      defaultOpen
    >
      <div style={contentScrollStyle}>
        <div style={summaryCardStyle}>
          <strong style={{ color: "#102a43" }}>{props.workOrder.summary}</strong>
          <div style={summaryMetaStyle}>建议处理角色：{props.workOrder.assignee_placeholder}</div>
          <p style={{ margin: "10px 0 0", lineHeight: 1.8, color: "#243b53" }}>{props.workOrder.risk_notice}</p>
        </div>

        <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
          {stepItems.length > 0 ? (
            stepItems.map((item, index) => (
              <div key={`${item.kind}-${index}`} style={stepCardStyle}>
                <div style={stepHeadStyle}>
                  <strong>
                    {index + 1}. {item.title || (item.kind === "check" ? "检查项" : "处置动作")}
                  </strong>
                  <span style={stepMetaPillStyle}>{priorityLabel[item.priority]}优先</span>
                </div>
                <p style={{ margin: "8px 0 10px", lineHeight: 1.75, color: "#243b53" }}>{item.instruction}</p>
                <div style={stepMetaStyle}>
                  预计耗时：{item.estimated_duration_minutes} 分钟
                  {item.action_type ? ` ｜ 动作类型：${actionTypeLabel[item.action_type]}` : ""}
                </div>
              </div>
            ))
          ) : (
            <ol style={{ margin: 0, paddingLeft: 18, display: "grid", gap: 8 }}>
              {props.workOrder.steps.map((item) => (
                <li key={item} style={{ lineHeight: 1.75, color: "#243b53" }}>
                  {item}
                </li>
              ))}
            </ol>
          )}
        </div>

        {props.workOrder.evidence_references?.length ? (
          <details style={detailsStyle}>
            <summary style={summaryToggleStyle}>证据引用（{props.workOrder.evidence_references.length}）</summary>
            <div style={{ marginTop: 10, color: "#486581", lineHeight: 1.8 }}>
              {props.workOrder.evidence_references.join(" / ")}
            </div>
          </details>
        ) : null}

        {props.workOrder.safety_notes?.length ? (
          <details style={detailsStyle}>
            <summary style={summaryToggleStyle}>安全注意事项（{props.workOrder.safety_notes.length}）</summary>
            <ul style={{ margin: "10px 0 0", paddingLeft: 18, display: "grid", gap: 6 }}>
              {props.workOrder.safety_notes.map((item) => (
                <li key={item} style={{ lineHeight: 1.75, color: "#243b53" }}>
                  {item}
                </li>
              ))}
            </ul>
          </details>
        ) : null}

        {props.validationResult ? (
          <section style={validationStyle(props.validationResult.status)}>
            <strong>校验状态：{props.validationResult.status === "ready_to_submit" ? "可提交" : "需修订"}</strong>
            <p style={{ margin: "8px 0 0", color: "#243b53", lineHeight: 1.75 }}>
              {props.validationResult.requires_approval ? "该工单需要进入人工审批流程。" : "该工单可以进入执行与反馈流程。"}
            </p>
            {props.validationResult.issues.length > 0 ? (
              <ul style={{ margin: "10px 0 0", paddingLeft: 18, display: "grid", gap: 6 }}>
                {props.validationResult.issues.map((issue) => (
                  <li key={`${issue.field}-${issue.message}`} style={{ lineHeight: 1.75 }}>
                    {issue.message}
                    {issue.suggested_fix ? ` 建议：${issue.suggested_fix}` : ""}
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
        ) : null}
      </div>
    </CollapsibleSection>
  );
}

const contentScrollStyle = {
  maxHeight: 500,
  overflowY: "auto" as const,
  paddingRight: 4,
} as const;

const summaryCardStyle = {
  borderRadius: 18,
  padding: 14,
  background: "#f8fafc",
  border: "1px solid rgba(148, 163, 184, 0.16)",
} as const;

const summaryMetaStyle = {
  marginTop: 8,
  color: "#5f7285",
  fontSize: 13,
} as const;

const stepCardStyle = {
  borderRadius: 18,
  padding: 14,
  background: "#fbfcfe",
  border: "1px solid rgba(148, 163, 184, 0.16)",
} as const;

const stepHeadStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  flexWrap: "wrap" as const,
  alignItems: "center",
} as const;

const stepMetaPillStyle = {
  borderRadius: 999,
  padding: "4px 10px",
  background: "#eef2f7",
  color: "#486581",
  fontSize: 12,
  fontWeight: 700,
} as const;

const stepMetaStyle = {
  color: "#64748b",
  fontSize: 12,
} as const;

const detailsStyle = {
  marginTop: 14,
  borderRadius: 18,
  padding: 14,
  background: "#ffffff",
  border: "1px solid rgba(148, 163, 184, 0.16)",
} as const;

const summaryToggleStyle = {
  cursor: "pointer",
  fontWeight: 800,
  color: "#102a43",
} as const;

function validationStyle(status: "ready_to_submit" | "needs_revision") {
  return {
    marginTop: 14,
    borderRadius: 18,
    padding: 14,
    background: status === "ready_to_submit" ? "#f0fdf4" : "#fff7ed",
    border: `1px solid ${status === "ready_to_submit" ? "rgba(34, 197, 94, 0.18)" : "rgba(245, 158, 11, 0.22)"}`,
    color: "#102a43",
  } as const;
}
