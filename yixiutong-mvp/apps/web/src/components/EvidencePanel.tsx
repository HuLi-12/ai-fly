type EvidenceItem = {
  evidence_id: string;
  source_type: string;
  title: string;
  snippet: string;
  score: number;
  source_path?: string;
  retrieval_method?: "keyword" | "semantic" | "hybrid";
  keyword_score?: number;
  semantic_score?: number;
  rerank_score?: number;
};

export function EvidencePanel(props: { evidence: EvidenceItem[] }) {
  return (
    <section style={panelStyle}>
      <h2 style={{ marginTop: 0 }}>证据召回</h2>
      <div style={{ display: "grid", gap: 12 }}>
        {props.evidence.map((item, index) => (
          <article key={item.evidence_id || `${item.title}-${index}`} style={cardStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
              <strong>{item.title}</strong>
              <span style={{ color: "#5a6d7d" }}>
                {item.source_type} / {item.retrieval_method ?? "semantic"} / 最终分 {item.score.toFixed(2)}
              </span>
            </div>
            <p style={{ marginBottom: 10, lineHeight: 1.7 }}>{item.snippet}</p>
            <div style={metaRowStyle}>
              <span>关键词 {Number(item.keyword_score ?? 0).toFixed(2)}</span>
              <span>语义 {Number(item.semantic_score ?? 0).toFixed(2)}</span>
              <span>重排 {Number(item.rerank_score ?? 0).toFixed(2)}</span>
            </div>
            {item.source_path ? (
              <p style={{ marginBottom: 0, marginTop: 10, color: "#6a7f90", fontSize: 12, wordBreak: "break-all" }}>
                来源路径：{item.source_path}
              </p>
            ) : null}
          </article>
        ))}
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
  padding: 14,
  borderRadius: 16,
  background: "#f7fafc",
  border: "1px solid rgba(12, 52, 83, 0.08)"
} as const;

const metaRowStyle = {
  display: "flex",
  gap: 12,
  flexWrap: "wrap",
  color: "#5a6d7d",
  fontSize: 12
} as const;
