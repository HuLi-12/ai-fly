import { useEffect, useState } from "react";
import type { ReactNode } from "react";

type Props = {
  requestId: string;
  workOrderId?: string;
  initialActions: string[];
  confirmLoading: boolean;
  feedbackLoading: boolean;
  confirmMessage: string;
  feedbackMessage: string;
  onConfirm: (payload: { approved: boolean; editedActions: string[]; operatorNote: string }) => Promise<void>;
  onSubmitFeedback: (payload: { feedbackType: string; feedbackText: string; finalResolution: string }) => Promise<void>;
};

function parseActions(value: string): string[] {
  return value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function ReviewPanel(props: Props) {
  const [editedActionsText, setEditedActionsText] = useState("");
  const [operatorNote, setOperatorNote] = useState("");
  const [feedbackType, setFeedbackType] = useState("业务复核");
  const [feedbackText, setFeedbackText] = useState("");
  const [finalResolution, setFinalResolution] = useState("");

  useEffect(() => {
    setEditedActionsText(props.initialActions.join("\n"));
    setOperatorNote("");
    setFeedbackText("");
    setFinalResolution("");
    setFeedbackType("业务复核");
  }, [props.initialActions, props.requestId, props.workOrderId]);

  return (
    <section style={panelStyle}>
      <div style={headerStyle}>
        <div>
          <div style={eyebrowStyle}>Review Loop</div>
          <h2 style={{ marginTop: 8, marginBottom: 8 }}>审批与回填闭环</h2>
          <p style={{ margin: 0, color: "#56697b", lineHeight: 1.7 }}>
            在这里确认 Agent 草案、写入审批意见，并将现场最终处置结果回填进案例闭环。
          </p>
        </div>
        <div style={metaCardStyle}>
          <div>
            请求号：<code>{props.requestId}</code>
          </div>
          {props.workOrderId ? (
            <div style={{ marginTop: 6 }}>
              工单号：<code>{props.workOrderId}</code>
            </div>
          ) : null}
        </div>
      </div>

      <div style={sectionGridStyle}>
        <section style={sectionCardStyle}>
          <h3 style={sectionTitleStyle}>审批调整</h3>
          <FieldBlock label="调整后的处置动作" hint="每行一条，审批通过时会以这里的动作为准。">
            <textarea rows={6} value={editedActionsText} onChange={(event) => setEditedActionsText(event.target.value)} style={fieldStyle} />
          </FieldBlock>
          <FieldBlock label="审批备注" hint="说明通过、驳回或要求修改的原因。">
            <textarea
              rows={3}
              value={operatorNote}
              onChange={(event) => setOperatorNote(event.target.value)}
              placeholder="例如：建议保留停机复核，并增加温度测点交叉校验。"
              style={fieldStyle}
            />
          </FieldBlock>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 16 }}>
            <button
              type="button"
              disabled={props.confirmLoading}
              onClick={() => props.onConfirm({ approved: true, editedActions: parseActions(editedActionsText), operatorNote })}
              style={approveButtonStyle}
            >
              {props.confirmLoading ? "提交中..." : "通过审批"}
            </button>
            <button
              type="button"
              disabled={props.confirmLoading}
              onClick={() => props.onConfirm({ approved: false, editedActions: parseActions(editedActionsText), operatorNote })}
              style={rejectButtonStyle}
            >
              {props.confirmLoading ? "提交中..." : "驳回重审"}
            </button>
          </div>

          {props.confirmMessage ? <div style={successBannerStyle}>{props.confirmMessage}</div> : null}
        </section>

        <section style={sectionCardStyle}>
          <h3 style={sectionTitleStyle}>结果回填</h3>
          <FieldBlock label="反馈类型">
            <select value={feedbackType} onChange={(event) => setFeedbackType(event.target.value)} style={fieldStyle}>
              <option value="业务复核">业务复核</option>
              <option value="质量回填">质量回填</option>
              <option value="工艺跟踪">工艺跟踪</option>
            </select>
          </FieldBlock>

          <FieldBlock label="反馈说明" hint="记录建议是否可用、现场是否安全、是否需要补充约束。">
            <textarea
              rows={3}
              value={feedbackText}
              onChange={(event) => setFeedbackText(event.target.value)}
              placeholder="例如：建议基本可用，但需在执行前补充安全隔离确认。"
              style={fieldStyle}
            />
          </FieldBlock>

          <FieldBlock label="最终处置结果" hint="这一项会直接影响案例是否回灌为闭环经验。">
            <textarea
              rows={4}
              value={finalResolution}
              onChange={(event) => setFinalResolution(event.target.value)}
              placeholder="例如：已更换轴承并复测通过，设备恢复运行。"
              style={fieldStyle}
            />
          </FieldBlock>

          <button
            type="button"
            disabled={props.feedbackLoading}
            onClick={() => props.onSubmitFeedback({ feedbackType, feedbackText, finalResolution })}
            style={saveButtonStyle}
          >
            {props.feedbackLoading ? "保存中..." : "回填反馈"}
          </button>

          {props.feedbackMessage ? <div style={successBannerStyle}>{props.feedbackMessage}</div> : null}
        </section>
      </div>
    </section>
  );
}

function FieldBlock(props: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label style={{ display: "grid", gap: 8 }}>
      <div style={{ fontWeight: 700, color: "#17344a" }}>{props.label}</div>
      {props.children}
      {props.hint ? <div style={{ fontSize: 12, color: "#607388", lineHeight: 1.6 }}>{props.hint}</div> : null}
    </label>
  );
}

const panelStyle = {
  background: "linear-gradient(180deg, rgba(255,255,255,0.98), rgba(246,249,252,0.95))",
  borderRadius: 28,
  padding: 24,
  border: "1px solid rgba(10, 58, 92, 0.1)",
  boxShadow: "0 24px 54px rgba(19, 37, 56, 0.08)",
} as const;

const headerStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 18,
  flexWrap: "wrap" as const,
  alignItems: "flex-start",
} as const;

const eyebrowStyle = {
  fontSize: 12,
  letterSpacing: 2,
  textTransform: "uppercase" as const,
  color: "#8b4a10",
  fontWeight: 800,
} as const;

const metaCardStyle = {
  borderRadius: 18,
  padding: "14px 16px",
  background: "#fff8ef",
  border: "1px solid rgba(160, 96, 21, 0.12)",
  color: "#5b4a38",
  minWidth: 220,
} as const;

const sectionGridStyle = {
  display: "grid",
  gap: 18,
  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
  marginTop: 20,
} as const;

const sectionCardStyle = {
  borderRadius: 22,
  padding: 18,
  background: "#fbfdff",
  border: "1px solid rgba(10, 58, 92, 0.08)",
  display: "grid",
  gap: 14,
  alignContent: "start" as const,
} as const;

const sectionTitleStyle = {
  margin: 0,
} as const;

const fieldStyle = {
  width: "100%",
  borderRadius: 16,
  border: "1px solid rgba(10, 58, 92, 0.14)",
  padding: "13px 14px",
  fontSize: 14,
  boxSizing: "border-box" as const,
  background: "#fff",
} as const;

const approveButtonStyle = {
  border: 0,
  borderRadius: 999,
  padding: "12px 18px",
  fontWeight: 800,
  cursor: "pointer",
  color: "#fff",
  background: "linear-gradient(135deg, #19704b, #10936d)",
  boxShadow: "0 16px 28px rgba(25, 112, 75, 0.2)",
} as const;

const rejectButtonStyle = {
  border: 0,
  borderRadius: 999,
  padding: "12px 18px",
  fontWeight: 800,
  cursor: "pointer",
  color: "#fff",
  background: "linear-gradient(135deg, #a53b24, #d96c17)",
  boxShadow: "0 16px 28px rgba(165, 59, 36, 0.18)",
} as const;

const saveButtonStyle = {
  marginTop: 4,
  border: 0,
  borderRadius: 999,
  padding: "12px 18px",
  fontWeight: 800,
  cursor: "pointer",
  color: "#fff",
  background: "linear-gradient(135deg, #0f4c81, #2d66b3)",
  boxShadow: "0 16px 28px rgba(15, 76, 129, 0.18)",
} as const;

const successBannerStyle = {
  borderRadius: 16,
  padding: "12px 14px",
  background: "#edf9f2",
  border: "1px solid rgba(22, 108, 67, 0.14)",
  color: "#17603a",
  lineHeight: 1.7,
} as const;
