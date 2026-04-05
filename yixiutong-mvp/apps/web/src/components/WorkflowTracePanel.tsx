type TraceItem = {
  node: string;
  status: "completed" | "warning" | "fallback" | "retry";
  summary: string;
  detail: string;
};

const nodeLabels: Record<string, string> = {
  route: "智能路由",
  retrieve: "首轮检索",
  retrieve_retry: "二次检索",
  diagnose: "诊断生成",
  trace: "证据追溯",
  score: "置信度评分",
  second_opinion: "二次校正",
  draft_work_order: "工单起草",
  validate: "工单校验",
  repair_work_order: "草案修复",
  respond: "结果组装"
};

const statusMeta = {
  completed: { label: "已完成", color: "#146c43", background: "#edf9f2" },
  warning: { label: "需关注", color: "#9a6700", background: "#fff7e8" },
  retry: { label: "已重试", color: "#0d5c7d", background: "#eef5fb" },
  fallback: { label: "兜底结果", color: "#b23b2a", background: "#fff2f1" }
} as const;

export function WorkflowTracePanel(props: { executionTrace: TraceItem[] }) {
  return (
    <section style={panelStyle}>
      <h2 style={{ marginTop: 0 }}>执行过程</h2>
      <div style={{ display: "grid", gap: 12 }}>
        {props.executionTrace.map((item, index) => {
          const meta = statusMeta[item.status];
          return (
            <article key={`${item.node}-${index}`} style={cardStyle}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
                <strong>{nodeLabels[item.node] ?? item.node}</strong>
                <span
                  style={{
                    padding: "4px 10px",
                    borderRadius: 999,
                    color: meta.color,
                    background: meta.background,
                    fontSize: 12,
                    fontWeight: 700
                  }}
                >
                  {meta.label}
                </span>
              </div>
              <p style={{ marginTop: 8, marginBottom: item.detail ? 8 : 0, lineHeight: 1.7 }}>{item.summary}</p>
              {item.detail ? <div style={{ color: "#5a6d7d", fontSize: 12, lineHeight: 1.6 }}>{item.detail}</div> : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}

const panelStyle = {
  background: "#fff",
  borderRadius: 22,
  padding: 20,
  border: "1px solid rgba(12, 52, 83, 0.12)"
} as const;

const cardStyle = {
  borderRadius: 14,
  padding: 14,
  background: "#f7fafc",
  border: "1px solid rgba(12, 52, 83, 0.08)"
} as const;
