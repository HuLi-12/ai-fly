import type { CSSProperties } from "react";
import type { SceneType } from "../services/api";

type Props = {
  sceneType: SceneType;
  faultCode: string;
  symptomText: string;
  deviceType: string;
  contextNotes: string;
  validationErrors: {
    faultCode?: string;
    symptomText?: string;
    deviceType?: string;
  };
  canSubmit: boolean;
  draftAvailable: boolean;
  onSceneTypeChange: (value: SceneType) => void;
  onFaultCodeChange: (value: string) => void;
  onSymptomTextChange: (value: string) => void;
  onDeviceTypeChange: (value: string) => void;
  onContextNotesChange: (value: string) => void;
  onSubmit: () => void;
  onApplyDemoPreset: () => void;
  onRestoreDraft: () => void;
  onClearDraft: () => void;
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

const sceneHints: Record<SceneType, string> = {
  fault_diagnosis: "适用于设备告警、振动异常、温升异常等故障诊断场景。",
  process_deviation: "适用于参数漂移、热处理偏差、批次冻结等工艺场景。",
  quality_inspection: "适用于终检缺陷、隔离处置、MRB 前置判断等质量场景。"
};

export function InputPanel(props: Props) {
  return (
    <section style={panelStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
        <div>
          <h2 style={{ marginTop: 0, marginBottom: 8 }}>Agent 业务输入</h2>
          <p style={{ margin: 0, color: "#5a6d7d", lineHeight: 1.6 }}>
            将故障、工艺偏差或质检异常按统一结构提交给 Agent，系统会自动联动检索、诊断、工单和审批流程。
          </p>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button onClick={props.onApplyDemoPreset} type="button" style={ghostButtonStyle}>
            加载示例
          </button>
          <button onClick={props.onRestoreDraft} type="button" disabled={!props.draftAvailable} style={ghostButtonStyle}>
            恢复草稿
          </button>
          <button onClick={props.onClearDraft} type="button" disabled={!props.draftAvailable} style={ghostButtonStyle}>
            清除草稿
          </button>
        </div>
      </div>

      <div style={{ marginTop: 12, padding: 12, borderRadius: 14, background: "#f7fafc", color: "#4d6172", lineHeight: 1.7 }}>
        当前场景提示：{sceneHints[props.sceneType]}
        {props.draftAvailable ? <strong style={{ marginLeft: 8, color: "#0d5c7d" }}>检测到本场景草稿，可直接恢复。</strong> : null}
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
          <input
            value={props.faultCode}
            onChange={(event) => props.onFaultCodeChange(event.target.value)}
            placeholder="例如：E-204 / PROC-118 / QA-305"
            style={inputStyle(Boolean(props.validationErrors.faultCode))}
          />
          <FieldHint text={props.validationErrors.faultCode ?? "建议按场景填写标准编号，便于检索和路由。"} tone={props.validationErrors.faultCode ? "error" : "normal"} />
        </label>

        <label>
          <div style={{ marginBottom: 6 }}>设备 / 工位对象</div>
          <input
            value={props.deviceType}
            onChange={(event) => props.onDeviceTypeChange(event.target.value)}
            placeholder="例如：航空装配工位 / 热处理设备 / 终检工位"
            style={inputStyle(Boolean(props.validationErrors.deviceType))}
          />
          <FieldHint text={props.validationErrors.deviceType ?? "建议写明设备、工位或产线对象。"} tone={props.validationErrors.deviceType ? "error" : "normal"} />
        </label>

        <label>
          <div style={{ marginBottom: 6 }}>异常现象</div>
          <textarea
            value={props.symptomText}
            onChange={(event) => props.onSymptomTextChange(event.target.value)}
            placeholder="描述现场症状、偏差表现或质量异常，例如：设备运行时振动异常，伴随温度升高。"
            rows={4}
            style={inputStyle(Boolean(props.validationErrors.symptomText))}
          />
          <FieldHint text={props.validationErrors.symptomText ?? "建议描述现象、趋势和触发条件。"} tone={props.validationErrors.symptomText ? "error" : "normal"} />
        </label>

        <label>
          <div style={{ marginBottom: 6 }}>补充上下文</div>
          <textarea
            value={props.contextNotes}
            onChange={(event) => props.onContextNotesChange(event.target.value)}
            placeholder="可补充班次、批次、工位、交接记录、材料批号等信息。"
            rows={3}
            style={fieldStyle}
          />
        </label>
      </div>

      <button onClick={props.onSubmit} disabled={props.loading || !props.canSubmit} type="button" style={primaryButtonStyle(props.loading || !props.canSubmit)}>
        {props.loading ? "Agent 分析中..." : "提交 Agent 分析"}
      </button>
    </section>
  );
}

function FieldHint(props: { text: string; tone: "error" | "normal" }) {
  return (
    <div style={{ marginTop: 6, color: props.tone === "error" ? "#b23b2a" : "#5a6d7d", fontSize: 12, lineHeight: 1.6 }}>
      {props.text}
    </div>
  );
}

function inputStyle(hasError: boolean): CSSProperties {
  return {
    ...fieldStyle,
    border: hasError ? "1px solid rgba(178, 59, 42, 0.48)" : fieldStyle.border
  };
}

const ghostButtonStyle = {
  borderRadius: 999,
  border: "1px solid rgba(12, 52, 83, 0.14)",
  padding: "10px 14px",
  background: "#fff",
  cursor: "pointer",
  fontWeight: 700,
  color: "#13384d"
} as const;

function primaryButtonStyle(disabled: boolean) {
  return {
    marginTop: 16,
    border: 0,
    borderRadius: 999,
    padding: "12px 18px",
    fontSize: 14,
    fontWeight: 700,
    cursor: disabled ? "not-allowed" : "pointer",
    color: "#fff",
    opacity: disabled ? 0.72 : 1,
    background: "linear-gradient(135deg, #0d5c7d, #1a7f64)"
  } as const;
}
