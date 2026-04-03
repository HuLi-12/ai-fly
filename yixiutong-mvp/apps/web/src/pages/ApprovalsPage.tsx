import { useEffect } from "react";
import { ReviewPanel } from "../components/ReviewPanel";
import type { WorkspaceController } from "../hooks/useYixiutongWorkspace";

type Props = {
  workspace: WorkspaceController;
};

export function ApprovalsPage(props: Props) {
  const { workspace } = props;

  useEffect(() => {
    if (!workspace.selectedWorkOrder && workspace.approvals[0]) {
      void workspace.openWorkOrder(workspace.approvals[0].work_order_id);
    }
  }, [workspace.approvals]);

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <section style={heroStyle}>
        <div style={{ fontSize: 12, letterSpacing: 2, textTransform: "uppercase", opacity: 0.74 }}>审批待办</div>
        <h1 style={{ marginBottom: 10 }}>待办审批箱</h1>
        <p style={{ marginBottom: 0, maxWidth: 880, lineHeight: 1.7 }}>
          待办箱现在只展示仍需处理的审批任务。已经通过或驳回的记录不会继续占据待办位，而是沉淀到工单详情里的审批历史中。
        </p>
      </section>

      <section style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
        <StatCard title="待办审批" value={String(workspace.approvals.length)} tone="warn" />
        <StatCard title="待审批工单" value={String(workspace.workOrders.filter((item) => item.status_bucket === "pending_approval").length)} tone="warn" />
        <StatCard title="驳回重审" value={String(workspace.workOrders.filter((item) => item.status_bucket === "rework").length)} tone="error" />
        <StatCard title="已进入执行" value={String(workspace.workOrders.filter((item) => item.status_bucket === "pending_execution").length)} tone="ok" />
      </section>

      <div style={{ display: "grid", gap: 20, gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", alignItems: "start" }}>
        <article style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>我的待办</h2>
          <div style={scrollAreaStyle}>
            {workspace.approvals.length ? (
              workspace.approvals.map((item) => (
                <button
                  key={item.approval_id}
                  type="button"
                  onClick={() => void workspace.openWorkOrder(item.work_order_id)}
                  style={{
                    ...approvalCardStyle,
                    borderColor:
                      workspace.selectedWorkOrder?.work_order_id === item.work_order_id
                        ? "rgba(170,117,35,0.4)"
                        : "rgba(9,52,84,0.08)"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                    <strong>{item.title}</strong>
                    <span style={pendingPillStyle}>{item.status_label}</span>
                  </div>
                  <div style={{ marginTop: 8, color: "#5a6d7d" }}>
                    {item.scene_label} / {item.assignee_name} / {item.priority}优先级
                  </div>
                  <div style={{ marginTop: 8, color: "#5a6d7d", lineHeight: 1.6 }}>{item.comment}</div>
                </button>
              ))
            ) : (
              <p style={{ margin: 0, color: "#5a6d7d" }}>当前没有待办审批，说明需要人工审核的任务已经处理完毕。</p>
            )}
          </div>
        </article>

        <article style={panelStyle}>
          {workspace.selectedWorkOrder ? (
            <div style={scrollAreaStyle}>
              <section style={{ display: "grid", gap: 10 }}>
                <h2 style={{ marginTop: 0, marginBottom: 0 }}>{workspace.selectedWorkOrder.title}</h2>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <Tag text={workspace.selectedWorkOrder.scene_label} />
                  <Tag text={workspace.selectedWorkOrder.status_bucket_label} />
                  <Tag text={`审批 ${workspace.selectedWorkOrder.approval_status}`} />
                </div>
              </section>

              <div style={{ display: "grid", gap: 10, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", marginTop: 18 }}>
                <InfoRow title="工单状态" value={workspace.selectedWorkOrder.status} />
                <InfoRow title="审批状态" value={workspace.selectedWorkOrder.approval_status} />
                <InfoRow title="摘要" value={workspace.selectedWorkOrder.summary} />
                <InfoRow title="最新说明" value={workspace.selectedWorkOrder.latest_note} />
              </div>

              <div style={{ marginTop: 20 }}>
                <ReviewPanel
                  requestId={workspace.selectedWorkOrder.request_id}
                  workOrderId={workspace.selectedWorkOrder.work_order_id}
                  initialActions={workspace.selectedWorkOrder.diagnosis.recommended_actions}
                  confirmLoading={workspace.decisionLoading}
                  feedbackLoading={workspace.feedbackLoading}
                  confirmMessage={workspace.decisionMessage}
                  feedbackMessage={workspace.feedbackMessage}
                  onConfirm={async (payload) => {
                    await workspace.decideSelectedWorkOrder({
                      approved: payload.approved,
                      comment: payload.operatorNote,
                      editedActions: payload.editedActions
                    });
                  }}
                  onSubmitFeedback={workspace.submitWorkOrderFeedback}
                />
              </div>

              <section style={{ display: "grid", gap: 10, marginTop: 20 }}>
                <h3 style={{ margin: 0 }}>审批历史</h3>
                {workspace.selectedWorkOrder.approvals.length ? (
                  workspace.selectedWorkOrder.approvals.map((item) => (
                    <div key={item.approval_id} style={historyCardStyle}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                        <strong>{item.title}</strong>
                        <span>{item.status_label}</span>
                      </div>
                      <div style={{ marginTop: 6, color: "#5a6d7d" }}>
                        {item.assignee_name} / {item.scene_label}
                      </div>
                      <div style={{ marginTop: 6, color: "#5a6d7d", lineHeight: 1.6 }}>{item.comment}</div>
                    </div>
                  ))
                ) : (
                  <p style={{ margin: 0, color: "#5a6d7d" }}>当前工单还没有审批记录。</p>
                )}
              </section>
            </div>
          ) : (
            <p style={{ margin: 0, color: "#5a6d7d" }}>请选择左侧待办查看详情。</p>
          )}
        </article>
      </div>
    </div>
  );
}

function StatCard(props: { title: string; value: string; tone: "ok" | "warn" | "error" }) {
  const palette = {
    ok: "linear-gradient(135deg, #0f5f85, #1d8a74)",
    warn: "linear-gradient(135deg, #83590f, #c0842d)",
    error: "linear-gradient(135deg, #8c3827, #c75a46)"
  } as const;

  return (
    <article style={{ borderRadius: 22, padding: 18, color: "#fff", background: palette[props.tone] }}>
      <div style={{ fontSize: 13, letterSpacing: 1 }}>{props.title}</div>
      <div style={{ marginTop: 12, fontSize: 32, fontWeight: 800 }}>{props.value}</div>
    </article>
  );
}

function Tag(props: { text: string }) {
  return <span style={tagStyle}>{props.text}</span>;
}

function InfoRow(props: { title: string; value: string }) {
  return (
    <div style={infoRowStyle}>
      <strong style={{ display: "block" }}>{props.title}</strong>
      <span style={{ display: "block", marginTop: 6, color: "#5a6d7d", lineHeight: 1.6 }}>{props.value}</span>
    </div>
  );
}

const heroStyle = {
  borderRadius: 28,
  padding: 28,
  color: "#fff",
  background: "linear-gradient(125deg, rgba(83,57,16,0.98), rgba(170,117,35,0.92) 54%, rgba(209,159,72,0.86))"
} as const;

const panelStyle = {
  background: "rgba(255,255,255,0.92)",
  border: "1px solid rgba(9,52,84,0.1)",
  borderRadius: 24,
  padding: 20,
  boxShadow: "0 18px 40px rgba(20, 37, 55, 0.06)"
} as const;

const scrollAreaStyle = {
  display: "grid",
  gap: 12,
  maxHeight: "68vh",
  overflowY: "auto" as const,
  paddingRight: 4
};

const approvalCardStyle = {
  border: "1px solid rgba(9,52,84,0.08)",
  borderRadius: 18,
  padding: 16,
  background: "#fff8ef",
  textAlign: "left" as const,
  cursor: "pointer"
};

const pendingPillStyle = {
  borderRadius: 999,
  padding: "6px 10px",
  background: "#fff1d6",
  color: "#9a6200",
  fontSize: 12,
  fontWeight: 700
} as const;

const tagStyle = {
  borderRadius: 999,
  padding: "6px 10px",
  background: "#f2f6f9",
  color: "#23445c",
  fontSize: 12,
  fontWeight: 700
} as const;

const infoRowStyle = {
  padding: 14,
  borderRadius: 16,
  background: "#f7fafc",
  border: "1px solid rgba(9,52,84,0.08)"
} as const;

const historyCardStyle = {
  border: "1px solid rgba(9,52,84,0.08)",
  borderRadius: 16,
  padding: 14,
  background: "#f7fafc"
} as const;
