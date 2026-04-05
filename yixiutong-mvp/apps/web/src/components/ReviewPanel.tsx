import { useEffect, useState } from "react";

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

const fieldStyle = {
  width: "100%",
  borderRadius: 12,
  border: "1px solid rgba(12, 52, 83, 0.18)",
  padding: "12px 14px",
  fontSize: 14,
  boxSizing: "border-box" as const
};

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
    <section style={{ background: "#fff", borderRadius: 22, padding: 20, border: "1px solid rgba(12, 52, 83, 0.12)" }}>
      <h2 style={{ marginTop: 0 }}>审批与反馈闭环</h2>
      <p style={{ lineHeight: 1.7 }}>
        请求号：<code>{props.requestId}</code>
        {props.workOrderId ? (
          <>
            {" "}
            | 工单号：<code>{props.workOrderId}</code>
          </>
        ) : null}
      </p>

      <div style={{ display: "grid", gap: 12 }}>
        <label>
          <div style={{ marginBottom: 6 }}>调整后的处置动作</div>
          <textarea rows={6} value={editedActionsText} onChange={(event) => setEditedActionsText(event.target.value)} style={fieldStyle} />
        </label>

        <label>
          <div style={{ marginBottom: 6 }}>审批备注</div>
          <textarea rows={3} value={operatorNote} onChange={(event) => setOperatorNote(event.target.value)} placeholder="说明通过或驳回的原因" style={fieldStyle} />
        </label>
      </div>

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

      {props.confirmMessage ? <p style={{ marginTop: 16, marginBottom: 0, color: "#146c43" }}>{props.confirmMessage}</p> : null}

      <hr style={{ border: 0, borderTop: "1px solid rgba(12, 52, 83, 0.12)", margin: "24px 0" }} />

      <div style={{ display: "grid", gap: 12 }}>
        <label>
          <div style={{ marginBottom: 6 }}>反馈类型</div>
          <select value={feedbackType} onChange={(event) => setFeedbackType(event.target.value)} style={fieldStyle}>
            <option value="业务复核">业务复核</option>
            <option value="质量回填">质量回填</option>
            <option value="工艺跟踪">工艺跟踪</option>
          </select>
        </label>

        <label>
          <div style={{ marginBottom: 6 }}>反馈说明</div>
          <textarea
            rows={3}
            value={feedbackText}
            onChange={(event) => setFeedbackText(event.target.value)}
            placeholder="记录建议是否可用、是否缺少关键步骤、现场是否安全。"
            style={fieldStyle}
          />
        </label>

        <label>
          <div style={{ marginBottom: 6 }}>最终处置结果</div>
          <textarea
            rows={3}
            value={finalResolution}
            onChange={(event) => setFinalResolution(event.target.value)}
            placeholder="记录最终检修、返工、让步放行或隔离结果。"
            style={fieldStyle}
          />
        </label>
      </div>

      <button type="button" disabled={props.feedbackLoading} onClick={() => props.onSubmitFeedback({ feedbackType, feedbackText, finalResolution })} style={saveButtonStyle}>
        {props.feedbackLoading ? "保存中..." : "回填反馈"}
      </button>

      {props.feedbackMessage ? <p style={{ marginTop: 16, marginBottom: 0, color: "#146c43" }}>{props.feedbackMessage}</p> : null}
    </section>
  );
}

const approveButtonStyle = {
  border: 0,
  borderRadius: 999,
  padding: "12px 18px",
  fontWeight: 700,
  cursor: "pointer",
  color: "#fff",
  background: "linear-gradient(135deg, #1a7f64, #0e9960)"
} as const;

const rejectButtonStyle = {
  border: 0,
  borderRadius: 999,
  padding: "12px 18px",
  fontWeight: 700,
  cursor: "pointer",
  color: "#fff",
  background: "linear-gradient(135deg, #b23b2a, #d35400)"
} as const;

const saveButtonStyle = {
  marginTop: 16,
  border: 0,
  borderRadius: 999,
  padding: "12px 18px",
  fontWeight: 700,
  cursor: "pointer",
  color: "#fff",
  background: "linear-gradient(135deg, #0d5c7d, #2356a3)"
} as const;
