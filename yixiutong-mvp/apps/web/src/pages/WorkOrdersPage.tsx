import { useState } from "react";
import type { WorkOrderListItem } from "../services/api";
import type { WorkspaceController } from "../hooks/useYixiutongWorkspace";

type Props = {
  workspace: WorkspaceController;
};

const statusTabs = [
  { key: "all", label: "全部工单" },
  { key: "pending_approval", label: "待审批" },
  { key: "pending_execution", label: "待执行" },
  { key: "in_progress", label: "处理中" },
  { key: "completed", label: "已完成" },
  { key: "rework", label: "驳回重审" }
] as const;

export function WorkOrdersPage(props: Props) {
  const { workspace } = props;
  const [keyword, setKeyword] = useState("");
  const [activeTab, setActiveTab] = useState<(typeof statusTabs)[number]["key"]>("all");

  const workOrders = workspace.workOrders.filter((item) => {
    if (activeTab !== "all" && item.status_bucket !== activeTab) {
      return false;
    }
    if (!keyword.trim()) {
      return true;
    }
    const lowered = keyword.trim().toLowerCase();
    return [item.title, item.summary, item.scene_label, item.symptom_text, item.assignee_name].some((field) =>
      field.toLowerCase().includes(lowered)
    );
  });

  const selectedWorkOrderId = workspace.selectedWorkOrder?.work_order_id;

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <section style={heroStyle}>
        <div style={{ fontSize: 12, letterSpacing: 2, textTransform: "uppercase", opacity: 0.74 }}>工单中心</div>
        <h1 style={{ marginBottom: 10 }}>工单列表与详情</h1>
        <p style={{ marginBottom: 0, maxWidth: 880, lineHeight: 1.7 }}>
          这里不再只是简单列表，而是按工单阶段来分栏查看。审批、执行、反馈和最终闭环都会回写到工单中心，形成系统的事实主线。
        </p>
      </section>

      <section style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
        {statusTabs.map((tab) => {
          const count =
            tab.key === "all" ? workspace.workOrders.length : workspace.workOrders.filter((item) => item.status_bucket === tab.key).length;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              style={{
                ...statCardStyle,
                background: activeTab === tab.key ? "linear-gradient(135deg, #0f5f85, #1d8a74)" : "#f7fafc",
                color: activeTab === tab.key ? "#fff" : "#17334a"
              }}
            >
              <div style={{ fontSize: 13, letterSpacing: 1 }}>{tab.label}</div>
              <div style={{ marginTop: 10, fontSize: 30, fontWeight: 800 }}>{count}</div>
            </button>
          );
        })}
      </section>

      <div style={{ display: "grid", gap: 20, gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", alignItems: "start" }}>
        <article style={panelStyle}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
            <div>
              <h2 style={{ margin: 0 }}>工单清单</h2>
              <p style={{ marginTop: 8, marginBottom: 0, color: "#5a6d7d" }}>按标题、摘要、场景、异常描述或处理人搜索。</p>
            </div>
            <input
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="搜索工单"
              style={inputStyle}
            />
          </div>

          <div style={scrollAreaStyle}>
            {workOrders.length ? (
              workOrders.map((item) => (
                <button
                  key={item.work_order_id}
                  type="button"
                  onClick={() => void workspace.openWorkOrder(item.work_order_id)}
                  style={{
                    ...workOrderCardStyle,
                    borderColor:
                      selectedWorkOrderId === item.work_order_id ? "rgba(13,92,125,0.45)" : "rgba(9,52,84,0.08)",
                    background: selectedWorkOrderId === item.work_order_id ? "#eef7fb" : "#f7fafc"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                    <strong>{item.title}</strong>
                    <span style={statusPillStyle(item.status_bucket)}>{item.status_bucket_label}</span>
                  </div>
                  <div style={{ marginTop: 8, color: "#5a6d7d", lineHeight: 1.6 }}>{item.summary}</div>
                  <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <MetaTag text={item.scene_label} />
                    <MetaTag text={`${item.priority}优先级`} />
                    <MetaTag text={item.assignee_name} />
                  </div>
                  <div style={{ marginTop: 10, color: "#5a6d7d", fontSize: 13 }}>
                    当前状态：{item.status} / 审批：{item.approval_status}
                  </div>
                </button>
              ))
            ) : (
              <p style={{ margin: 0, color: "#5a6d7d" }}>当前筛选条件下没有工单。</p>
            )}
          </div>
        </article>

        <article style={panelStyle}>
          {workspace.selectedWorkOrder ? (
            <div style={scrollAreaStyle}>
              <section style={{ display: "grid", gap: 10 }}>
                <h2 style={{ marginTop: 0, marginBottom: 0 }}>{workspace.selectedWorkOrder.title}</h2>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <MetaTag text={workspace.selectedWorkOrder.scene_label} />
                  <MetaTag text={workspace.selectedWorkOrder.status_bucket_label} />
                  <MetaTag text={`风险 ${workspace.selectedWorkOrder.risk_level}`} />
                  <MetaTag text={`通道 ${workspace.selectedWorkOrder.provider_used}`} />
                </div>
              </section>

              <section style={detailGridStyle}>
                <InfoRow title="工单编号" value={workspace.selectedWorkOrder.work_order_id} />
                <InfoRow title="发起人" value={`${workspace.selectedWorkOrder.applicant_name} / ${workspace.selectedWorkOrder.applicant_role}`} />
                <InfoRow title="处理席位" value={`${workspace.selectedWorkOrder.assignee_name} / ${workspace.selectedWorkOrder.assignee_role}`} />
                <InfoRow title="当前状态" value={`${workspace.selectedWorkOrder.status} / ${workspace.selectedWorkOrder.approval_status}`} />
              </section>

              <section style={sectionStyle}>
                <h3 style={sectionTitleStyle}>异常描述</h3>
                <p style={paragraphStyle}>{workspace.selectedWorkOrder.symptom_text}</p>
              </section>

              <section style={sectionStyle}>
                <h3 style={sectionTitleStyle}>最新说明</h3>
                <p style={paragraphStyle}>{workspace.selectedWorkOrder.latest_note}</p>
              </section>

              <section style={sectionStyle}>
                <h3 style={sectionTitleStyle}>建议处置步骤</h3>
                <ol style={listStyle}>
                  {workspace.selectedWorkOrder.diagnosis.recommended_actions.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ol>
              </section>

              <section style={sectionStyle}>
                <h3 style={sectionTitleStyle}>证据摘要</h3>
                <div style={{ display: "grid", gap: 10 }}>
                  {workspace.selectedWorkOrder.evidence.map((item) => (
                    <div key={`${item.source_type}-${item.title}`} style={evidenceCardStyle}>
                      <strong>{item.title}</strong>
                      <div style={{ marginTop: 6, color: "#5a6d7d", lineHeight: 1.6 }}>{item.snippet}</div>
                    </div>
                  ))}
                </div>
              </section>

              <section style={sectionStyle}>
                <h3 style={sectionTitleStyle}>审批历史</h3>
                <div style={{ display: "grid", gap: 10 }}>
                  {workspace.selectedWorkOrder.approvals.length ? (
                    workspace.selectedWorkOrder.approvals.map((item) => (
                      <div key={item.approval_id} style={approvalHistoryCardStyle}>
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
                    <p style={{ margin: 0, color: "#5a6d7d" }}>当前工单没有审批记录。</p>
                  )}
                </div>
              </section>

              {workspace.selectedWorkOrder.final_resolution ? (
                <section style={sectionStyle}>
                  <h3 style={sectionTitleStyle}>最终结论</h3>
                  <p style={paragraphStyle}>{workspace.selectedWorkOrder.final_resolution}</p>
                </section>
              ) : null}
            </div>
          ) : (
            <p style={{ margin: 0, color: "#5a6d7d" }}>请选择左侧工单查看详情。</p>
          )}
        </article>
      </div>
    </div>
  );
}

function MetaTag(props: { text: string }) {
  return <span style={metaTagStyle}>{props.text}</span>;
}

function InfoRow(props: { title: string; value: string }) {
  return (
    <div style={infoRowStyle}>
      <strong style={{ display: "block" }}>{props.title}</strong>
      <span style={{ display: "block", marginTop: 6, color: "#5a6d7d", lineHeight: 1.6 }}>{props.value}</span>
    </div>
  );
}

function statusPillStyle(statusBucket: WorkOrderListItem["status_bucket"]) {
  const palette: Record<string, { background: string; color: string }> = {
    pending_approval: { background: "#fff5e8", color: "#a56500" },
    pending_execution: { background: "#edf6ff", color: "#0d5c7d" },
    in_progress: { background: "#eefaf4", color: "#146c43" },
    completed: { background: "#eef4ef", color: "#2e5d37" },
    rework: { background: "#fff2f1", color: "#b23b2a" }
  };
  const tone = palette[statusBucket] ?? palette.pending_execution;
  return {
    borderRadius: 999,
    padding: "6px 10px",
    background: tone.background,
    color: tone.color,
    fontWeight: 700,
    fontSize: 12
  } as const;
}

const heroStyle = {
  borderRadius: 28,
  padding: 28,
  color: "#fff",
  background: "linear-gradient(125deg, rgba(24,58,93,0.98), rgba(50,98,150,0.92) 54%, rgba(72,153,179,0.86))"
} as const;

const panelStyle = {
  background: "rgba(255,255,255,0.92)",
  border: "1px solid rgba(9,52,84,0.1)",
  borderRadius: 24,
  padding: 20,
  boxShadow: "0 18px 40px rgba(20, 37, 55, 0.06)"
} as const;

const statCardStyle = {
  border: "1px solid rgba(9,52,84,0.08)",
  borderRadius: 22,
  padding: 18,
  textAlign: "left" as const,
  cursor: "pointer"
};

const inputStyle = {
  minWidth: 220,
  borderRadius: 999,
  border: "1px solid rgba(9,52,84,0.12)",
  padding: "10px 14px"
} as const;

const scrollAreaStyle = {
  display: "grid",
  gap: 12,
  marginTop: 18,
  maxHeight: "68vh",
  overflowY: "auto" as const,
  paddingRight: 4
};

const workOrderCardStyle = {
  border: "1px solid rgba(9,52,84,0.08)",
  borderRadius: 18,
  padding: 16,
  background: "#f7fafc",
  textAlign: "left" as const,
  cursor: "pointer"
};

const metaTagStyle = {
  borderRadius: 999,
  padding: "6px 10px",
  background: "#f2f6f9",
  color: "#23445c",
  fontSize: 12,
  fontWeight: 700
} as const;

const detailGridStyle = {
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
  marginTop: 18
} as const;

const infoRowStyle = {
  padding: 14,
  borderRadius: 16,
  background: "#f7fafc",
  border: "1px solid rgba(9,52,84,0.08)"
} as const;

const sectionStyle = {
  display: "grid",
  gap: 10,
  marginTop: 18
} as const;

const sectionTitleStyle = {
  margin: 0
} as const;

const paragraphStyle = {
  margin: 0,
  color: "#22384d",
  lineHeight: 1.8
} as const;

const listStyle = {
  margin: 0,
  paddingLeft: 20,
  display: "grid",
  gap: 8,
  color: "#22384d",
  lineHeight: 1.8
} as const;

const evidenceCardStyle = {
  border: "1px solid rgba(9,52,84,0.08)",
  borderRadius: 16,
  padding: 14,
  background: "#f7fafc"
} as const;

const approvalHistoryCardStyle = {
  border: "1px solid rgba(9,52,84,0.08)",
  borderRadius: 16,
  padding: 14,
  background: "#fff8ef"
} as const;
