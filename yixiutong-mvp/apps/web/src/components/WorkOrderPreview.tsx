type StepItem = {
  kind: "check" | "action";
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

export function WorkOrderPreview(props: { workOrder: WorkOrderDraft; validationResult?: ValidationResult }) {
  const stepItems = props.workOrder.step_items ?? [];

  return (
    <section style={panelStyle}>
      <h2 style={{ marginTop: 0 }}>工单草案</h2>
      <p>
        <strong>{props.workOrder.summary}</strong>
      </p>

      {stepItems.length > 0 ? (
        <div style={{ display: "grid", gap: 10 }}>
          {stepItems.map((item, index) => (
            <div key={`${item.kind}-${index}`} style={stepCardStyle}>
              <strong>
                {index + 1}. {item.kind === "check" ? "检查" : "动作"}
              </strong>
              <p style={{ margin: "6px 0 10px", lineHeight: 1.7 }}>{item.instruction}</p>
              <span style={metaStyle}>
                优先级：{item.priority} / 预计耗时：{item.estimated_duration_minutes} 分钟
                {item.action_type ? ` / 动作类型：${item.action_type}` : ""}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <ol style={{ paddingLeft: 20, display: "grid", gap: 8 }}>
          {props.workOrder.steps.map((item) => (
            <li key={item} style={{ lineHeight: 1.7 }}>
              {item}
            </li>
          ))}
        </ol>
      )}

      <p style={{ lineHeight: 1.7 }}>{props.workOrder.risk_notice}</p>
      <p>建议处理角色：{props.workOrder.assignee_placeholder}</p>

      {props.workOrder.evidence_references && props.workOrder.evidence_references.length > 0 ? (
        <p style={metaStyle}>证据引用：{props.workOrder.evidence_references.join(" / ")}</p>
      ) : null}

      {props.workOrder.safety_notes && props.workOrder.safety_notes.length > 0 ? (
        <div style={{ marginTop: 12 }}>
          <strong>安全注意事项</strong>
          <ul style={{ paddingLeft: 20, marginBottom: 0 }}>
            {props.workOrder.safety_notes.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {props.validationResult ? (
        <div style={validationStyle(props.validationResult.status)}>
          <strong>校验状态：{props.validationResult.status}</strong>
          <p style={{ margin: "8px 0 0" }}>
            {props.validationResult.requires_approval ? "该工单要求人工审批。" : "该工单可进入提交流程。"}
          </p>
          {props.validationResult.issues.length > 0 ? (
            <ul style={{ margin: "8px 0 0", paddingLeft: 20 }}>
              {props.validationResult.issues.map((issue) => (
                <li key={`${issue.field}-${issue.message}`}>
                  {issue.message}
                  {issue.suggested_fix ? ` 建议：${issue.suggested_fix}` : ""}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

const panelStyle = {
  background: "#fff",
  borderRadius: 22,
  padding: 20,
  border: "1px solid rgba(12, 52, 83, 0.12)"
} as const;

const stepCardStyle = {
  borderRadius: 14,
  padding: 12,
  background: "#f7fafc",
  border: "1px solid rgba(12, 52, 83, 0.08)"
} as const;

const metaStyle = {
  color: "#5a6d7d",
  fontSize: 12
} as const;

function validationStyle(status: "ready_to_submit" | "needs_revision") {
  return {
    marginTop: 14,
    borderRadius: 14,
    padding: 14,
    background: status === "ready_to_submit" ? "#edf9f2" : "#fff4e8",
    border: `1px solid ${status === "ready_to_submit" ? "rgba(11, 122, 75, 0.18)" : "rgba(185, 92, 0, 0.18)"}`
  } as const;
}
