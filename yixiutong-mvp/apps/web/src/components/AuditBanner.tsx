export function AuditBanner(props: {
  requiresHumanConfirmation: boolean;
  providerUsed: string;
  confidenceScore?: number;
  approvalReasons?: string[];
}) {
  return (
    <section
      style={{
        background: props.requiresHumanConfirmation ? "#fff4e8" : "#edf9f2",
        borderRadius: 22,
        padding: 20,
        border: `1px solid ${props.requiresHumanConfirmation ? "rgba(185, 92, 0, 0.18)" : "rgba(11, 122, 75, 0.18)"}`
      }}
    >
      <h2 style={{ marginTop: 0 }}>审批闸门</h2>
      <p>推理通道：{props.providerUsed}</p>
      {typeof props.confidenceScore === "number" ? <p>当前置信度：{props.confidenceScore.toFixed(1)}</p> : null}
      <p>
        {props.requiresHumanConfirmation
          ? "当前结果命中了人工审批条件，必须进入待办审批箱后才能继续流转。"
          : "当前结果可直接进入执行与反馈环节。"}
      </p>
      {props.approvalReasons && props.approvalReasons.length > 0 ? (
        <ul style={{ margin: "8px 0 0", paddingLeft: 20 }}>
          {props.approvalReasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
      ) : null}
      {props.providerUsed === "heuristic_fallback" ? (
        <p style={{ marginBottom: 0 }}>
          当前结果由启发式兜底链路生成，正式使用时建议优先启用本地模型或已配置的主通道。
        </p>
      ) : null}
    </section>
  );
}
