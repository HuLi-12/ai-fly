export function AuditBanner(props: {
  requiresHumanConfirmation: boolean;
  providerUsed: string;
  confidenceScore?: number;
  approvalReasons?: string[];
}) {
  return (
    <section style={panelStyle(props.requiresHumanConfirmation)}>
      <div style={headStyle}>
        <div>
          <div style={eyebrowStyle}>Approval Gate</div>
          <h2 style={{ marginTop: 8, marginBottom: 8 }}>审批闸门</h2>
        </div>
        <div style={chipRowStyle}>
          <span style={chipStyle}>{props.requiresHumanConfirmation ? "需要人工审批" : "可直接流转"}</span>
          <span style={chipStyle}>推理通道：{props.providerUsed}</span>
          {typeof props.confidenceScore === "number" ? <span style={chipStyle}>置信度：{props.confidenceScore.toFixed(1)}</span> : null}
        </div>
      </div>

      <p style={paragraphStyle}>
        {props.requiresHumanConfirmation
          ? "当前结果命中了人工审批条件，必须进入待办审批箱后才能继续流转。"
          : "当前结果满足自动放行条件，可以直接进入执行与反馈环节。"}
      </p>

      {props.approvalReasons?.length ? (
        <div style={{ display: "grid", gap: 8, marginTop: 10 }}>
          {props.approvalReasons.map((reason) => (
            <div key={reason} style={reasonRowStyle}>
              {reason}
            </div>
          ))}
        </div>
      ) : null}

      {props.providerUsed === "heuristic_fallback" ? (
        <p style={{ marginTop: 12, marginBottom: 0, color: "#7c2d12", lineHeight: 1.75 }}>
          当前结果由启发式兜底链路生成，正式使用时建议优先启用本地模型或可用的主通道。
        </p>
      ) : null}
    </section>
  );
}

function panelStyle(requiresApproval: boolean) {
  return {
    borderRadius: 22,
    padding: 18,
    background: requiresApproval ? "#fffaf0" : "#f5fbf8",
    border: `1px solid ${requiresApproval ? "rgba(245, 158, 11, 0.2)" : "rgba(34, 197, 94, 0.18)"}`,
    boxShadow: "0 12px 24px rgba(15, 23, 42, 0.04)",
  } as const;
}

const headStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 14,
  flexWrap: "wrap" as const,
  alignItems: "flex-start",
} as const;

const eyebrowStyle = {
  fontSize: 12,
  letterSpacing: 2,
  textTransform: "uppercase" as const,
  color: "#486581",
  fontWeight: 800,
} as const;

const chipRowStyle = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap" as const,
} as const;

const chipStyle = {
  borderRadius: 999,
  padding: "6px 10px",
  background: "#ffffff",
  color: "#486581",
  fontSize: 12,
  fontWeight: 700,
  border: "1px solid rgba(148, 163, 184, 0.18)",
} as const;

const paragraphStyle = {
  margin: 0,
  color: "#243b53",
  lineHeight: 1.8,
} as const;

const reasonRowStyle = {
  borderRadius: 14,
  padding: 12,
  background: "#ffffff",
  border: "1px solid rgba(148, 163, 184, 0.16)",
  color: "#243b53",
  lineHeight: 1.7,
} as const;
