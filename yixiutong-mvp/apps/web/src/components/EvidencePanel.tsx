import { CollapsibleSection } from "./CollapsibleSection";

type EvidenceItem = {
  evidence_id: string;
  source_type: string;
  title: string;
  snippet: string;
  score: number;
  source_path?: string;
  retrieval_backend?: string;
  retrieval_method?: "keyword" | "semantic" | "hybrid";
  keyword_score?: number;
  semantic_score?: number;
  rerank_score?: number;
  model_rerank_score?: number;
};

const sourceTypeLabel: Record<string, string> = {
  manual: "维修手册",
  case: "历史案例",
  case_memory: "闭环案例记忆",
  template: "模板条目",
  knowledge: "知识条目",
};

const methodLabel = {
  keyword: "关键词",
  semantic: "语义",
  hybrid: "混合",
} as const;

export function EvidencePanel(props: { evidence: EvidenceItem[] }) {
  return (
    <CollapsibleSection
      title="证据回召"
      subtitle={`本轮共回召 ${props.evidence.length} 条证据，默认收起，便于先聚焦主诊断结果。`}
      badge={props.evidence.length ? `${props.evidence.length} 条证据` : "无证据"}
      defaultOpen={false}
      bodyStyle={{ paddingTop: 6 }}
    >
      <div style={scrollBodyStyle}>
        <div style={{ display: "grid", gap: 12 }}>
          {props.evidence.map((item, index) => (
            <article key={item.evidence_id || `${item.title}-${index}`} style={cardStyle}>
              <div style={headRowStyle}>
                <strong style={{ color: "#102a43" }}>{item.title}</strong>
                <div style={chipRowStyle}>
                  <span style={chipStyle}>{sourceTypeLabel[item.source_type] ?? item.source_type}</span>
                  <span style={chipStyle}>{methodLabel[item.retrieval_method ?? "semantic"]}</span>
                  <span style={scoreChipStyle}>最终分 {item.score.toFixed(2)}</span>
                </div>
              </div>

              <p style={snippetStyle}>{item.snippet}</p>

              <div style={metaRowStyle}>
                <span>关键词 {Number(item.keyword_score ?? 0).toFixed(2)}</span>
                <span>语义 {Number(item.semantic_score ?? 0).toFixed(2)}</span>
                <span>复排 {Number(item.rerank_score ?? 0).toFixed(2)}</span>
                <span>模型复排 {Number(item.model_rerank_score ?? 0).toFixed(2)}</span>
              </div>

              {item.retrieval_backend ? <div style={pathStyle}>检索后端：{item.retrieval_backend}</div> : null}
              {item.source_path ? <div style={pathStyle}>来源路径：{item.source_path}</div> : null}
            </article>
          ))}
        </div>
      </div>
    </CollapsibleSection>
  );
}

const scrollBodyStyle = {
  maxHeight: 440,
  overflowY: "auto" as const,
  paddingRight: 4,
} as const;

const cardStyle = {
  borderRadius: 18,
  padding: 16,
  background: "#fbfcfe",
  border: "1px solid rgba(148, 163, 184, 0.18)",
} as const;

const headRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  flexWrap: "wrap" as const,
  alignItems: "flex-start",
} as const;

const chipRowStyle = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap" as const,
} as const;

const chipStyle = {
  borderRadius: 999,
  padding: "5px 10px",
  background: "#eef2f7",
  color: "#486581",
  fontSize: 12,
  fontWeight: 700,
} as const;

const scoreChipStyle = {
  borderRadius: 999,
  padding: "5px 10px",
  background: "#dbeafe",
  color: "#1d4ed8",
  fontSize: 12,
  fontWeight: 700,
} as const;

const snippetStyle = {
  margin: "12px 0 10px",
  color: "#243b53",
  lineHeight: 1.8,
} as const;

const metaRowStyle = {
  display: "flex",
  gap: 10,
  flexWrap: "wrap" as const,
  color: "#5f7285",
  fontSize: 12,
} as const;

const pathStyle = {
  marginTop: 10,
  color: "#6b7d8f",
  fontSize: 12,
  wordBreak: "break-word" as const,
} as const;
