import type { SceneType } from "../services/api";
import { CollapsibleSection } from "./CollapsibleSection";

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
  quality_inspection: "质量处置",
};

const confidenceLabel = {
  high: "高",
  medium: "中",
  low: "低",
} as const;

const riskLabel = {
  high: "高风险",
  medium: "中风险",
  low: "低风险",
} as const;

export function DiagnosisPanel(props: {
  diagnosis: Diagnosis;
  riskLevel: string;
  sceneType: SceneType;
  confidence?: Confidence;
  triggeredRules?: TriggeredRule[];
  routeConfidence?: number;
  routeReason?: string;
  routeSignals?: string[];
}) {
  return (
    <CollapsibleSection
      title="结构化分析建议"
      subtitle="把 Agent 的路由判断、风险等级、置信度和建议清单合并在一个主面板中，避免多个独立大卡片互相抢焦点。"
      badge={`${sceneLabel[props.sceneType]} / ${riskLabel[(props.riskLevel as keyof typeof riskLabel) ?? "medium"] || props.riskLevel}`}
      defaultOpen
    >
      <div style={contentScrollStyle}>
        <div style={metricGridStyle}>
          <MetricTile label="业务场景" value={sceneLabel[props.sceneType]} />
          <MetricTile label="风险等级" value={riskLabel[(props.riskLevel as keyof typeof riskLabel) ?? "medium"] || props.riskLevel} />
          <MetricTile
            label="置信度"
            value={props.confidence ? `${props.confidence.overall_score.toFixed(1)} / ${confidenceLabel[props.confidence.level]}` : "待计算"}
          />
        </div>

        {props.routeReason ? (
          <section style={infoCardStyle}>
            <strong style={{ color: "#102a43" }}>路由判断依据</strong>
            <p style={paragraphStyle}>{props.routeReason}</p>
            <div style={metaTextStyle}>
              路由置信度：{Number(props.routeConfidence ?? 0).toFixed(2)}
              {props.routeSignals && props.routeSignals.length ? ` ｜ 命中信号：${props.routeSignals.join(" / ")}` : ""}
            </div>
          </section>
        ) : null}

        {props.confidence ? (
          <section style={confidenceStyle(props.confidence.level)}>
            <strong>结论置信度：{props.confidence.overall_score.toFixed(1)}</strong>
            {props.confidence.warnings.length ? (
              <ul style={{ margin: "10px 0 0", paddingLeft: 18, display: "grid", gap: 6 }}>
                {props.confidence.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            ) : (
              <p style={{ margin: "8px 0 0", color: "#486581" }}>当前证据支持度较完整，本轮无需额外补充风险提示。</p>
            )}
          </section>
        ) : null}

        {props.triggeredRules?.length ? (
          <details style={detailsStyle}>
            <summary style={summaryStyle}>规则命中（{props.triggeredRules.length}）</summary>
            <div style={{ display: "grid", gap: 8, marginTop: 12 }}>
              {props.triggeredRules.map((rule) => (
                <div key={rule.rule_id} style={ruleCardStyle}>
                  <strong>{rule.rule_id}</strong>
                  <p style={{ margin: "6px 0", lineHeight: 1.7 }}>{rule.message}</p>
                  <span style={metaTextStyle}>关键词：{rule.matched_keywords.join(" / ") || "无"}</span>
                </div>
              ))}
            </div>
          </details>
        ) : null}

        <div style={{ display: "grid", gap: 12, marginTop: 14 }}>
          <ListCard title="可能原因" items={props.diagnosis.possible_causes} />
          <ListCard title="建议检查" items={props.diagnosis.recommended_checks} />
          <ListCard title="建议处置" items={props.diagnosis.recommended_actions} />
        </div>
      </div>
    </CollapsibleSection>
  );
}

function MetricTile(props: { label: string; value: string }) {
  return (
    <div style={metricTileStyle}>
      <div style={metricLabelStyle}>{props.label}</div>
      <strong style={metricValueStyle}>{props.value}</strong>
    </div>
  );
}

function ListCard(props: { title: string; items: string[] }) {
  return (
    <section style={listCardStyle}>
      <strong style={{ color: "#102a43" }}>{props.title}</strong>
      <ul style={{ margin: "10px 0 0", paddingLeft: 18, display: "grid", gap: 7 }}>
        {props.items.map((item) => (
          <li key={item} style={{ lineHeight: 1.75, color: "#243b53" }}>
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}

function confidenceStyle(level: "high" | "medium" | "low") {
  const palette = {
    high: { background: "#f0fdf4", border: "rgba(34, 197, 94, 0.2)" },
    medium: { background: "#fffbeb", border: "rgba(245, 158, 11, 0.22)" },
    low: { background: "#fef2f2", border: "rgba(239, 68, 68, 0.18)" },
  }[level];
  return {
    marginTop: 14,
    borderRadius: 18,
    padding: 14,
    background: palette.background,
    border: `1px solid ${palette.border}`,
    color: "#102a43",
  } as const;
}

const contentScrollStyle = {
  maxHeight: 520,
  overflowY: "auto" as const,
  paddingRight: 4,
} as const;

const metricGridStyle = {
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
} as const;

const metricTileStyle = {
  borderRadius: 18,
  padding: 14,
  background: "#f8fafc",
  border: "1px solid rgba(148, 163, 184, 0.16)",
} as const;

const metricLabelStyle = {
  fontSize: 12,
  color: "#64748b",
  letterSpacing: 1.1,
  textTransform: "uppercase" as const,
  fontWeight: 800,
} as const;

const metricValueStyle = {
  display: "block",
  marginTop: 8,
  color: "#102a43",
  fontSize: 16,
} as const;

const infoCardStyle = {
  marginTop: 14,
  borderRadius: 18,
  padding: 14,
  background: "#f8fafc",
  border: "1px solid rgba(148, 163, 184, 0.16)",
} as const;

const paragraphStyle = {
  margin: "8px 0",
  lineHeight: 1.8,
  color: "#243b53",
} as const;

const metaTextStyle = {
  color: "#64748b",
  fontSize: 12,
  lineHeight: 1.65,
} as const;

const detailsStyle = {
  marginTop: 14,
  borderRadius: 18,
  border: "1px solid rgba(148, 163, 184, 0.16)",
  padding: 14,
  background: "#ffffff",
} as const;

const summaryStyle = {
  cursor: "pointer",
  color: "#102a43",
  fontWeight: 800,
} as const;

const ruleCardStyle = {
  borderRadius: 14,
  padding: 12,
  background: "#f8fafc",
  border: "1px solid rgba(148, 163, 184, 0.14)",
} as const;

const listCardStyle = {
  borderRadius: 18,
  padding: 14,
  background: "#fbfcfe",
  border: "1px solid rgba(148, 163, 184, 0.16)",
} as const;
