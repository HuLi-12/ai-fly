import type { SceneType } from "../services/api";

type Diagnosis = {
  possible_causes: string[];
  recommended_checks: string[];
  recommended_actions: string[];
};

const sceneLabel: Record<SceneType, string> = {
  fault_diagnosis: "智能排故",
  process_deviation: "工艺偏差",
  quality_inspection: "质量处置"
};

export function DiagnosisPanel(props: { diagnosis: Diagnosis; riskLevel: string; sceneType: SceneType }) {
  return (
    <section style={panelStyle}>
      <h2 style={{ marginTop: 0 }}>结构化分析建议</h2>
      <p style={{ color: "#5a6d7d" }}>
        场景：{sceneLabel[props.sceneType]} | 风险等级：{props.riskLevel}
      </p>
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
          <li key={item} style={{ lineHeight: 1.7 }}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

const panelStyle = {
  background: "#fff",
  borderRadius: 22,
  padding: 20,
  border: "1px solid rgba(12, 52, 83, 0.12)"
} as const;
