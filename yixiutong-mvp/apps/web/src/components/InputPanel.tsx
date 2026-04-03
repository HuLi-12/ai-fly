import type { CSSProperties } from "react";
import type { SceneType } from "../services/api";

type Props = {
  sceneType: SceneType;
  faultCode: string;
  symptomText: string;
  deviceType: string;
  contextNotes: string;
  onSceneTypeChange: (value: SceneType) => void;
  onFaultCodeChange: (value: string) => void;
  onSymptomTextChange: (value: string) => void;
  onDeviceTypeChange: (value: string) => void;
  onContextNotesChange: (value: string) => void;
  onSubmit: () => void;
  onApplyDemoPreset: () => void;
  loading: boolean;
};

const panelStyle: CSSProperties = {
  background: "rgba(255,255,255,0.92)",
  border: "1px solid rgba(12, 52, 83, 0.12)",
  borderRadius: 22,
  padding: 20,
  boxShadow: "0 20px 50px rgba(22, 39, 58, 0.08)"
};

const fieldStyle: CSSProperties = {
  width: "100%",
  borderRadius: 14,
  border: "1px solid rgba(12, 52, 83, 0.18)",
  padding: "12px 14px",
  fontSize: 14,
  boxSizing: "border-box"
};

export function InputPanel(props: Props) {
  return (
    <section style={panelStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
        <div>
          <h2 style={{ marginTop: 0, marginBottom: 8 }}>Agent 业务输入</h2>
          <p style={{ margin: 0, color: "#5a6d7d", lineHeight: 1.6 }}>把故障、工艺偏差或质检异常按统一格式提交给 Agent，以便后续自动挂接工单和审批。</p>
        </div>
        <button onClick={props.onApplyDemoPreset} type="button" style={ghostButtonStyle}>
          载入示例
        </button>
      </div>
      <div style={{ display: "grid", gap: 12, marginTop: 16 }}>
        <label>
          <div style={{ marginBottom: 6 }}>业务场景</div>
          <select value={props.sceneType} onChange={(event) => props.onSceneTypeChange(event.target.value as SceneType)} style={fieldStyle}>
            <option value="fault_diagnosis">智能排故</option>
            <option value="process_deviation">工艺偏差</option>
            <option value="quality_inspection">质量处置</option>
          </select>
        </label>
        <label>
          <div style={{ marginBottom: 6 }}>问题编号 / 故障码</div>
          <input value={props.faultCode} onChange={(event) => props.onFaultCodeChange(event.target.value)} placeholder="例如：E-204 / PROC-118 / QA-305" style={fieldStyle} />
        </label>
        <label>
          <div style={{ marginBottom: 6 }}>设备 / 工位对象</div>
          <input value={props.deviceType} onChange={(event) => props.onDeviceTypeChange(event.target.value)} placeholder="例如：装配工位 / 固化设备 / 终检工位" style={fieldStyle} />
        </label>
        <label>
          <div style={{ marginBottom: 6 }}>异常现象</div>
          <textarea value={props.symptomText} onChange={(event) => props.onSymptomTextChange(event.target.value)} placeholder="描述现场症状、偏差表现或质量异常" rows={4} style={fieldStyle} />
        </label>
        <label>
          <div style={{ marginBottom: 6 }}>补充上下文</div>
          <textarea value={props.contextNotes} onChange={(event) => props.onContextNotesChange(event.target.value)} placeholder="班次、批次、工位、操作人交接、材料批号等" rows={3} style={fieldStyle} />
        </label>
      </div>
      <button onClick={props.onSubmit} disabled={props.loading} type="button" style={primaryButtonStyle(props.loading)}>
        {props.loading ? "Agent 分析中..." : "提交 Agent 分析"}
      </button>
    </section>
  );
}

const ghostButtonStyle = {
  borderRadius: 999,
  border: "1px solid rgba(12, 52, 83, 0.14)",
  padding: "10px 14px",
  background: "#fff",
  cursor: "pointer",
  fontWeight: 700,
  color: "#13384d"
};

function primaryButtonStyle(loading: boolean) {
  return {
    marginTop: 16,
    border: 0,
    borderRadius: 999,
    padding: "12px 18px",
    fontSize: 14,
    fontWeight: 700,
    cursor: loading ? "not-allowed" : "pointer",
    color: "#fff",
    background: "linear-gradient(135deg, #0d5c7d, #1a7f64)"
  } as const;
}
