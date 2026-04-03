type EvidenceItem = {
  source_type: string;
  title: string;
  snippet: string;
  score: number;
};

export function EvidencePanel(props: { evidence: EvidenceItem[] }) {
  return (
    <section style={panelStyle}>
      <h2 style={{ marginTop: 0 }}>证据召回</h2>
      <div style={{ display: "grid", gap: 12 }}>
        {props.evidence.map((item, index) => (
          <article key={`${item.title}-${index}`} style={cardStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
              <strong>{item.title}</strong>
              <span style={{ color: "#5a6d7d" }}>
                {item.source_type} / 相关度 {item.score.toFixed(2)}
              </span>
            </div>
            <p style={{ marginBottom: 0, lineHeight: 1.7 }}>{item.snippet}</p>
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
