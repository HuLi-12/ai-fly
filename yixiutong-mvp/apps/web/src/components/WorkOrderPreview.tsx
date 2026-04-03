type WorkOrderDraft = {
  summary: string;
  steps: string[];
  risk_notice: string;
  assignee_placeholder: string;
};

export function WorkOrderPreview(props: { workOrder: WorkOrderDraft }) {
  return (
    <section style={panelStyle}>
      <h2 style={{ marginTop: 0 }}>工单草案</h2>
      <p><strong>{props.workOrder.summary}</strong></p>
      <ol style={{ paddingLeft: 20, display: "grid", gap: 8 }}>
        {props.workOrder.steps.map((item) => (
          <li key={item} style={{ lineHeight: 1.7 }}>{item}</li>
        ))}
      </ol>
      <p style={{ lineHeight: 1.7 }}>{props.workOrder.risk_notice}</p>
      <p style={{ marginBottom: 0 }}>建议处理角色：{props.workOrder.assignee_placeholder}</p>
    </section>
  );
}

const panelStyle = {
  background: "#fff",
  borderRadius: 22,
  padding: 20,
  border: "1px solid rgba(12, 52, 83, 0.12)"
} as const;
