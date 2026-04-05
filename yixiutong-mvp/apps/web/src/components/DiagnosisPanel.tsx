import type { SceneType } from "../services/api";

type Diagnosis = {
  possible_causes: string[];
  recommended_checks: string[];
  recommended_actions: string[];
};

type Confidence = {
  overall_score: number;
  level: "high" | "medium" | "low";
  warnings: string[];
};

type TriggeredRule = {
  rule_id: string;
  risk_level: "low" | "medium" | "high";
  message: string;
  matched_keywords: string[];
};

const sceneLabel: Record<SceneType, string> = {
  fault_diagnosis: "智能排故",
  process_deviation: "工艺偏差",
  quality_inspection: "质量处置"
};

export function DiagnosisPanel(props: {
  diagnosis: Diagnosis;
  riskLevel: string;
  sceneType: SceneType;
  confidence?: Confidence;
  triggeredRules?: TriggeredRule[];
}) {
  return (
    <section style={panelStyle}>
      <h2 style={{ marginTop: 0 }}>结构化分析建议</h2>
      <p style={{ color: "#5a6d7d" }}>
        场景：{sceneLabel[props.sceneType]} | 风险等级：{props.riskLevel}
      </p>

      {props.confidence ? (
        <section style={bannerStyle(props.confidence.level)}>
          <strong>置信度 {props.confidence.overall_score.toFixed(1)}</strong>
          <span style={{ marginLeft: 10 }}>等级：{props.confidence.level}</span>
          {props.confidence.warnings.length > 0 ? (
            <ul style={{ margin: "10px 0 0", paddingLeft: 20 }}>
              {props.confidence.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      {props.triggeredRules && props.triggeredRules.length > 0 ? (
        <section style={{ marginTop: 18 }}>
          <h3 style={{ marginBottom: 10 }}>规则命中</h3>
          <div style={{ display: "grid", gap: 8 }}>
            {props.triggeredRules.map((rule) => (
              <div key={rule.rule_id} style={ruleCardStyle}>
                <strong>{rule.rule_id}</strong>
                <p style={{ margin: "6px 0" }}>{rule.message}</p>
                <span style={{ color: "#5a6d7d", fontSize: 12 }}>
                  关键词：{rule.matched_keywords.join(" / ") || "无"}
                </span>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <Block title="可能原因" items={props.diagnosis.possible_causes} />
      <Block title="建议检查" items={props.diagnosis.recommended_checks} />
      <Block title="建议处置" items={props.diagnosis.recommended_actions} />
    </section>
  );
}

function Block(props: { title: string; items: string[] }) {
  return (
    <section style={{ marginTop: 18 }}>
      <h3 style={{ marginBottom: 10 }}>{props.title}</h3>
      <ul style={{ margin: 0, paddingLeft: 20, display: "grid", gap: 8 }}>
        {props.items.map((item) => (
          <li key={item} style={{ lineHeight: 1.7 }}>
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}

function bannerStyle(level: "high" | "medium" | "low") {
  const palette = {
    high: { background: "#edf9f2", border: "rgba(11, 122, 75, 0.18)" },
    medium: { background: "#fff7e8", border: "rgba(185, 92, 0, 0.18)" },
    low: { background: "#fff1f1", border: "rgba(179, 41, 41, 0.18)" }
  }[level];
  return {
    marginTop: 10,
    padding: 14,
    borderRadius: 16,
    background: palette.background,
    border: `1px solid ${palette.border}`
  } as const;
}

const panelStyle = {
  background: "#fff",
  borderRadius: 22,
  padding: 20,
  border: "1px solid rgba(12, 52, 83, 0.12)"
} as const;

const ruleCardStyle = {
  padding: 12,
  borderRadius: 14,
  border: "1px solid rgba(12, 52, 83, 0.08)",
  background: "#f7fafc"
} as const;
