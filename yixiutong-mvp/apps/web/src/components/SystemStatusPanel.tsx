import type { ProviderCheck, SelfCheckResponse } from "../services/api";

export function SystemStatusPanel(props: { selfCheck: SelfCheckResponse | null; providerChecks: ProviderCheck[] }) {
  const primary = props.providerChecks.find((item) => item.channel === "primary");
  const fallback = props.providerChecks.find((item) => item.channel === "fallback");

  return (
    <section style={panelStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
        <div>
          <h2 style={{ marginTop: 0, marginBottom: 8 }}>系统状态</h2>
          <p style={subTextStyle}>这里只展示部署与运行真正需要关注的主通道、兜底通道和检索状态。</p>
        </div>
      </div>

      <div style={{ display: "grid", gap: 14, gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", marginTop: 16 }}>
        <StatusCard
          title="主推理通道"
          value={primary?.configured ? props.selfCheck?.provider ?? "已配置" : "未配置"}
          tone={primary?.reachable ? "ok" : "warn"}
          rows={[
            `可达性：${primary?.reachable ? "在线" : "未就绪"}`,
            `地址：${props.selfCheck?.primary_base_url || "未填写"}`,
            `详情：${primary?.detail ?? "等待检测"}`
          ]}
        />
        <StatusCard
          title="本地兜底通道"
          value={fallback?.configured ? props.selfCheck?.fallback_provider ?? "已配置" : "未配置"}
          tone={fallback?.reachable ? "ok" : "warn"}
          rows={[
            `可达性：${fallback?.reachable ? "在线" : "未就绪"}`,
            `地址：${props.selfCheck?.fallback_base_url || "未填写"}`,
            `详情：${fallback?.detail ?? "等待检测"}`
          ]}
        />
        <StatusCard
          title="本地模型"
          value={props.selfCheck?.local_model_present ? "已识别" : "未识别"}
          tone={props.selfCheck?.local_model_present ? "ok" : "warn"}
          rows={[
            `本地模型启用：${props.selfCheck?.local_model_enabled ? "是" : "否"}`,
            `Ollama 可执行文件：${props.selfCheck?.ollama_executable_present ? "已识别" : "未识别"}`,
            `路径：${props.selfCheck?.ollama_executable_path || "未记录"}`
          ]}
        />
        <StatusCard
          title="检索后端"
          value={props.selfCheck?.retrieval_vector_enabled ? "向量检索已启用" : "仅关键词模式"}
          tone={props.selfCheck?.retrieval_vector_enabled ? "ok" : "warn"}
          rows={[
            `Embedding Provider：${props.selfCheck?.retrieval_embedding_provider || "未配置"}`,
            `Embedding Model：${props.selfCheck?.retrieval_embedding_model || "未配置"}`,
            `模型复排：${props.selfCheck?.retrieval_model_rerank_enabled ? "已启用" : "未启用"}`
          ]}
        />
      </div>
    </section>
  );
}

function StatusCard(props: { title: string; value: string; rows: string[]; tone: "ok" | "warn" }) {
  return (
    <article
      style={{
        padding: 18,
        borderRadius: 20,
        background: props.tone === "ok" ? "#f2fbf7" : "#fff8ef",
        border: `1px solid ${props.tone === "ok" ? "rgba(15,122,85,0.12)" : "rgba(192,132,45,0.18)"}`
      }}
    >
      <div style={{ fontSize: 13, color: "#5a6d7d", textTransform: "uppercase", letterSpacing: 1 }}>{props.title}</div>
      <div style={{ marginTop: 10, fontSize: 24, fontWeight: 800 }}>{props.value}</div>
      <div style={{ display: "grid", gap: 8, marginTop: 14, color: "#4d6172", lineHeight: 1.6 }}>
        {props.rows.map((row) => (
          <div key={row}>{row}</div>
        ))}
      </div>
    </article>
  );
}

const panelStyle = {
  background: "rgba(255,255,255,0.92)",
  borderRadius: 24,
  padding: 20,
  border: "1px solid rgba(9,52,84,0.1)",
  boxShadow: "0 18px 40px rgba(20, 37, 55, 0.06)"
} as const;

const subTextStyle = {
  margin: 0,
  color: "#5a6d7d",
  lineHeight: 1.7
};
