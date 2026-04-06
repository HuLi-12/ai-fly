import type { CSSProperties, ReactNode } from "react";
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
  draftSavedAt: string | null;
  draftDirty: boolean;
  draftSource: "preset" | "draft" | "session";
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

const sceneHints: Record<SceneType, string> = {
  fault_diagnosis: "适用于设备报警、振动异常、温升异常等维修排故场景。",
  process_deviation: "适用于工艺参数漂移、热处理偏差、批次冻结等工艺场景。",
  quality_inspection: "适用于终检缺陷、隔离处置、MRB 前置判断等质量场景。"
};

export function InputPanel(props: Props) {
  const draftStatusText = buildDraftStatusText(props.draftAvailable, props.draftDirty, props.draftSource, props.draftSavedAt);

  return (
    <section style={panelStyle}>
      <div style={headerWrapStyle}>
        <div>
          <div style={eyebrowStyle}>Diagnosis Intake</div>
          <h2 style={{ marginTop: 8, marginBottom: 8 }}>分析请求输入</h2>
          <p style={descriptionStyle}>
            先选择业务场景，再补全故障码、设备对象和异常现象。场景切换会自动保留当前输入，示例预设和草稿恢复也不再互相覆盖。
          </p>
        </div>

        <div style={actionClusterStyle}>
          <ActionButton label="加载示例" onClick={props.onApplyDemoPreset} />
          <ActionButton label="恢复草稿" onClick={props.onRestoreDraft} disabled={!props.draftAvailable} />
          <ActionButton label="清除草稿" onClick={props.onClearDraft} disabled={!props.draftAvailable} subtle />
        </div>
      </div>

      <div style={hintBannerStyle}>
        <strong style={{ color: "#113b5b" }}>当前场景：</strong>
        <span>{sceneHints[props.sceneType]}</span>
        <span style={draftTextStyle}>{draftStatusText}</span>
      </div>

      <div style={gridStyle}>
        <FieldBlock label="业务场景">
          <select value={props.sceneType} onChange={(event) => props.onSceneTypeChange(event.target.value as SceneType)} style={fieldStyle}>
            <option value="fault_diagnosis">智能排故</option>
            <option value="process_deviation">工艺偏差</option>
            <option value="quality_inspection">质量处置</option>
          </select>
        </FieldBlock>

        <FieldBlock
          label="问题编号 / 故障码"
          hint={props.validationErrors.faultCode ?? "建议填写标准编号，便于检索和场景路由。"}
          error={Boolean(props.validationErrors.faultCode)}
        >
          <input
            value={props.faultCode}
            onChange={(event) => props.onFaultCodeChange(event.target.value)}
            placeholder="例如：E-204 / PROC-118 / QA-305"
            style={inputStyle(Boolean(props.validationErrors.faultCode))}
          />
        </FieldBlock>

        <FieldBlock
          label="设备 / 工位对象"
          hint={props.validationErrors.deviceType ?? "建议写明设备、工位或产线对象。"}
          error={Boolean(props.validationErrors.deviceType)}
        >
          <input
            value={props.deviceType}
            onChange={(event) => props.onDeviceTypeChange(event.target.value)}
            placeholder="例如：航空装配工位 / 热处理设备 / 终检工位"
            style={inputStyle(Boolean(props.validationErrors.deviceType))}
          />
        </FieldBlock>

        <div style={{ gridColumn: "1 / -1" }}>
          <FieldBlock
            label="异常现象"
            hint={props.validationErrors.symptomText ?? "建议描述异常表现、趋势和触发条件。"}
            error={Boolean(props.validationErrors.symptomText)}
          >
            <textarea
              value={props.symptomText}
              onChange={(event) => props.onSymptomTextChange(event.target.value)}
              placeholder="描述现场症状、偏差表现或质量异常，例如：设备运行时振动异常，并伴随温度升高。"
              rows={4}
              style={inputStyle(Boolean(props.validationErrors.symptomText))}
            />
          </FieldBlock>
        </div>

        <div style={{ gridColumn: "1 / -1" }}>
          <FieldBlock label="补充上下文" hint="可补充班次、批次、交接记录、材料批号、环境条件等信息。">
            <textarea
              value={props.contextNotes}
              onChange={(event) => props.onContextNotesChange(event.target.value)}
              placeholder="例如：夜班连续运行 6 小时后告警升级，最近更换过夹具或搬运工位。"
              rows={3}
              style={fieldStyle}
            />
          </FieldBlock>
        </div>
      </div>

      <div style={submitBarStyle}>
        <div style={{ color: "#546577", lineHeight: 1.7 }}>
          提交后会自动创建实时分析会话。顶部只展示用户真正需要的进度：当前阶段、当前代理，以及是否触发二次检索或二次校正。
        </div>
        <button onClick={props.onSubmit} disabled={props.loading || !props.canSubmit} type="button" style={primaryButtonStyle(props.loading || !props.canSubmit)}>
          {props.loading ? "分析会话启动中..." : "开始 Agent 分析"}
        </button>
      </div>
    </section>
  );
}

function buildDraftStatusText(
  draftAvailable: boolean,
  draftDirty: boolean,
  draftSource: "preset" | "draft" | "session",
  draftSavedAt: string | null
) {
  const timeText = draftSavedAt ? `最近保存：${formatDraftTime(draftSavedAt)}` : "";
  if (draftDirty) {
    return draftAvailable ? `当前输入有未保存变更，系统会自动保存。${timeText}` : "当前输入有未保存变更，系统会自动保存。";
  }
  if (draftSource === "draft") {
    return timeText ? `已恢复本场景草稿。${timeText}` : "已恢复本场景草稿。";
  }
  if (draftSource === "session" && draftAvailable) {
    return timeText ? `当前内容已自动保存。${timeText}` : "当前内容已自动保存。";
  }
  if (draftAvailable) {
    return timeText ? `检测到本场景存在可恢复草稿。${timeText}` : "检测到本场景存在可恢复草稿。";
  }
  return "当前为示例预设内容，可直接修改后开始分析。";
}

function formatDraftTime(value: string) {
  try {
    return new Date(value).toLocaleString("zh-CN", {
      hour12: false,
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit"
    });
  } catch {
    return value;
  }
}

function FieldBlock(props: { label: string; hint?: string; error?: boolean; children: ReactNode }) {
  return (
    <label style={{ display: "grid", gap: 8 }}>
      <div style={{ fontWeight: 700, color: "#15344c" }}>{props.label}</div>
      {props.children}
      {props.hint ? (
        <div style={{ fontSize: 12, lineHeight: 1.6, color: props.error ? "#b23b2a" : "#607388" }}>{props.hint}</div>
      ) : null}
    </label>
  );
}

function ActionButton(props: { label: string; onClick: () => void; disabled?: boolean; subtle?: boolean }) {
  return (
    <button
      onClick={props.onClick}
      type="button"
      disabled={props.disabled}
      style={{
        borderRadius: 999,
        border: props.subtle ? "1px dashed rgba(15, 76, 129, 0.22)" : "1px solid rgba(15, 76, 129, 0.14)",
        padding: "10px 14px",
        background: props.disabled ? "#f5f7fa" : "#fff",
        color: props.disabled ? "#8da0b3" : "#12395b",
        cursor: props.disabled ? "not-allowed" : "pointer",
        fontWeight: 700
      }}
    >
      {props.label}
    </button>
  );
}

function inputStyle(hasError: boolean): CSSProperties {
  return {
    ...fieldStyle,
    border: hasError ? "1px solid rgba(178, 59, 42, 0.45)" : fieldStyle.border,
    boxShadow: hasError ? "0 0 0 4px rgba(178, 59, 42, 0.08)" : "none"
  };
}

function primaryButtonStyle(disabled: boolean) {
  return {
    border: 0,
    borderRadius: 999,
    padding: "13px 22px",
    minWidth: 168,
    fontSize: 14,
    fontWeight: 800,
    cursor: disabled ? "not-allowed" : "pointer",
    color: "#fff",
    opacity: disabled ? 0.72 : 1,
    background: "linear-gradient(135deg, #0f4c81, #177b66 62%, #1da28b)",
    boxShadow: disabled ? "none" : "0 18px 32px rgba(15, 76, 129, 0.22)"
  } as const;
}

const panelStyle: CSSProperties = {
  background: "linear-gradient(180deg, rgba(255,255,255,0.98), rgba(245,249,252,0.95))",
  border: "1px solid rgba(10, 58, 92, 0.1)",
  borderRadius: 28,
  padding: 24,
  boxShadow: "0 24px 54px rgba(19, 37, 56, 0.08)"
};

const headerWrapStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 16,
  flexWrap: "wrap" as const,
  alignItems: "flex-start"
} as const;

const eyebrowStyle = {
  fontSize: 12,
  letterSpacing: 2,
  textTransform: "uppercase" as const,
  color: "#0f4c81",
  fontWeight: 800
} as const;

const descriptionStyle = {
  margin: 0,
  color: "#546577",
  lineHeight: 1.7,
  maxWidth: 640
} as const;

const actionClusterStyle = {
  display: "flex",
  gap: 8,
  flexWrap: "wrap" as const,
  alignItems: "center"
} as const;

const hintBannerStyle = {
  marginTop: 16,
  borderRadius: 18,
  padding: "14px 16px",
  background: "linear-gradient(135deg, rgba(220, 239, 252, 0.78), rgba(238, 247, 243, 0.92))",
  color: "#375066",
  lineHeight: 1.7,
  display: "grid",
  gap: 4
} as const;

const draftTextStyle = {
  color: "#0f4c81",
  fontWeight: 700
} as const;

const gridStyle = {
  display: "grid",
  gap: 16,
  gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
  marginTop: 18
} as const;

const fieldStyle: CSSProperties = {
  width: "100%",
  borderRadius: 16,
  border: "1px solid rgba(10, 58, 92, 0.14)",
  padding: "13px 14px",
  fontSize: 14,
  boxSizing: "border-box",
  background: "#fff"
};

const submitBarStyle = {
  marginTop: 20,
  display: "flex",
  justifyContent: "space-between",
  gap: 14,
  flexWrap: "wrap" as const,
  alignItems: "center"
} as const;
