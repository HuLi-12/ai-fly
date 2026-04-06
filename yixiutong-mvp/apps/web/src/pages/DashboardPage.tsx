import type { PortalModule } from "../hooks/useYixiutongWorkspace";
import type { LatestTodoItem, PortalOverviewResponse } from "../services/api";

type Props = {
  overview: PortalOverviewResponse | null;
  onOpenModule: (module: PortalModule) => void;
  onOpenWorkOrder: (workOrderId: string) => Promise<void>;
};

const quickEntries: Array<{ key: PortalModule; title: string; desc: string }> = [
  { key: "fault", title: "发起智能排故", desc: "从异常告警直接进入 Agent 分析与工单生成。" },
  { key: "approvals", title: "处理待办审批", desc: "集中查看仍待处理的审批任务和复核意见。" },
  { key: "work_orders", title: "进入工单中心", desc: "查看待执行、处理中、已完成和驳回重审工单。" },
  { key: "knowledge", title: "在线查阅资料", desc: "快速打开维修手册、案例和制度模板。" },
];

export function DashboardPage(props: Props) {
  const summary = props.overview?.summary;
  const latestTodos = props.overview?.latest_todos ?? [];

  return (
    <div style={{ display: "grid", gap: 18 }}>
      <section style={heroStyle}>
        <div>
          <div style={eyebrowStyle}>Portal Workspace</div>
          <h1 style={{ margin: "8px 0 10px" }}>业务工作台</h1>
          <p style={heroTextStyle}>
            工作台现在按真实业务流转展示待审批、待执行、处理中和待跟踪任务，不再把“最新待办”局限成审批列表。
            维修工程师、工艺工程师和质量工程师都会看到与自己当前角色相匹配的任务入口。
          </p>
        </div>
      </section>

      <section style={summaryGridStyle}>
        <SummaryCard title="工单总量" value={String(summary?.work_order_count ?? 0)} />
        <SummaryCard title="待审批" value={String(summary?.pending_approval_count ?? 0)} />
        <SummaryCard title="待执行" value={String(summary?.pending_execution_count ?? 0)} />
        <SummaryCard title="处理中" value={String(summary?.in_progress_count ?? 0)} />
        <SummaryCard title="已完成" value={String(summary?.completed_count ?? 0)} />
        <SummaryCard title="驳回重审" value={String(summary?.rework_count ?? 0)} />
      </section>

      <section style={contentGridStyle}>
        <article style={panelStyle}>
          <div style={sectionHeaderStyle}>
            <div>
              <div style={sectionEyebrowStyle}>Quick Access</div>
              <h2 style={{ margin: "8px 0 0" }}>快捷入口</h2>
            </div>
          </div>
          <div style={quickGridStyle}>
            {quickEntries.map((item) => (
              <button key={item.key} type="button" onClick={() => props.onOpenModule(item.key)} style={quickCardStyle}>
                <strong style={{ display: "block" }}>{item.title}</strong>
                <span style={quickDescStyle}>{item.desc}</span>
              </button>
            ))}
          </div>
        </article>

        <article style={panelStyle}>
          <div style={sectionHeaderStyle}>
            <div>
              <div style={sectionEyebrowStyle}>My Queue</div>
              <h2 style={{ margin: "8px 0 0" }}>最新待办</h2>
            </div>
            <span style={badgeStyle}>{latestTodos.length ? `${latestTodos.length} 项` : "当前为空"}</span>
          </div>

          <div style={todoListStyle}>
            {latestTodos.length ? (
              latestTodos.map((item) => (
                <button
                  key={item.todo_id}
                  type="button"
                  onClick={() => void props.onOpenWorkOrder(item.work_order_id).then(() => props.onOpenModule(item.target_module))}
                  style={todoCardStyle(item.task_type)}
                >
                  <div style={todoTopRowStyle}>
                    <div>
                      <strong style={{ display: "block" }}>{item.title}</strong>
                      <div style={todoMetaStyle}>
                        {item.scene_label} / 当前责任人 {item.assignee_name}
                      </div>
                    </div>
                    <span style={taskPillStyle(item.task_type)}>{taskTypeLabel(item)}</span>
                  </div>

                  <div style={todoSummaryStyle}>{item.summary}</div>

                  <div style={todoBottomRowStyle}>
                    <div style={todoInfoStyle}>
                      <span>{friendlyStatusLabel(item.status_label)}</span>
                    </div>
                    <span style={actionHintStyle}>{friendlyActionLabel(item.action_label)}</span>
                  </div>
                </button>
              ))
            ) : (
              <div style={emptyStyle}>
                当前没有需要你处理或跟踪的任务。新的审批、执行或处理中工单会优先出现在这里。
              </div>
            )}
          </div>
        </article>
      </section>

      <article style={panelStyle}>
        <div style={sectionHeaderStyle}>
          <div>
            <div style={sectionEyebrowStyle}>Recent Orders</div>
            <h2 style={{ margin: "8px 0 0" }}>最新工单</h2>
          </div>
        </div>

        <div style={workOrderListStyle}>
          {props.overview?.work_orders.length ? (
            props.overview.work_orders.map((item) => (
              <button
                key={item.work_order_id}
                type="button"
                onClick={() => void props.onOpenWorkOrder(item.work_order_id).then(() => props.onOpenModule("work_orders"))}
                style={workOrderCardStyle}
              >
                <div style={todoTopRowStyle}>
                  <strong>{item.title}</strong>
                  <span style={statusPillStyle}>{item.status_bucket_label}</span>
                </div>
                <div style={todoSummaryStyle}>{item.summary}</div>
                <div style={todoMetaStyle}>
                  {item.scene_label} / 处理岗位 {item.assignee_name}
                </div>
              </button>
            ))
          ) : (
            <div style={emptyStyle}>当前还没有工单。你可以先从业务席位发起一次 Agent 分析。</div>
          )}
        </div>
      </article>
    </div>
  );
}

function taskTypeLabel(item: LatestTodoItem) {
  if (item.task_type === "approval") {
    return "待审批";
  }
  if (item.task_type === "execution") {
    return "待执行";
  }
  if (item.task_type === "in_progress") {
    return "处理中";
  }
  return "待跟踪";
}

function friendlyStatusLabel(status: string) {
  if (status === "pending_execution") {
    return "待执行";
  }
  if (status === "in_progress") {
    return "处理中";
  }
  if (status === "tracking") {
    return "待跟踪";
  }
  return "待审批";
}

function friendlyActionLabel(action: string) {
  if (action === "open_execution") {
    return "去执行";
  }
  if (action === "resume_processing") {
    return "继续处理";
  }
  if (action === "view_progress") {
    return "查看进度";
  }
  return "去审批";
}

function SummaryCard(props: { title: string; value: string }) {
  return (
    <article style={summaryCardStyle}>
      <div style={summaryLabelStyle}>{props.title}</div>
      <div style={summaryValueStyle}>{props.value}</div>
    </article>
  );
}

function todoCardStyle(taskType: LatestTodoItem["task_type"]) {
  const tone =
    taskType === "approval"
      ? { background: "#fff9f0", border: "rgba(180, 83, 9, 0.16)" }
      : taskType === "execution"
        ? { background: "#f5fbff", border: "rgba(15, 76, 129, 0.16)" }
        : taskType === "in_progress"
          ? { background: "#f7fbf8", border: "rgba(47, 133, 90, 0.16)" }
          : { background: "#f8fafc", border: "rgba(100, 116, 139, 0.16)" };

  return {
    border: `1px solid ${tone.border}`,
    borderRadius: 18,
    padding: 16,
    background: tone.background,
    textAlign: "left" as const,
    cursor: "pointer",
  } as const;
}

function taskPillStyle(taskType: LatestTodoItem["task_type"]) {
  const tone =
    taskType === "approval"
      ? { background: "#ffedd5", color: "#b45309" }
      : taskType === "execution"
        ? { background: "#dbeafe", color: "#1d4ed8" }
        : taskType === "in_progress"
          ? { background: "#dcfce7", color: "#15803d" }
          : { background: "#e2e8f0", color: "#475569" };

  return {
    borderRadius: 999,
    padding: "6px 10px",
    background: tone.background,
    color: tone.color,
    fontSize: 12,
    fontWeight: 700,
    flexShrink: 0,
  } as const;
}

const heroStyle = {
  borderRadius: 26,
  padding: 24,
  background: "linear-gradient(180deg, #ffffff, #f7fafc)",
  border: "1px solid rgba(148, 163, 184, 0.18)",
  boxShadow: "0 16px 36px rgba(15, 23, 42, 0.05)",
} as const;

const eyebrowStyle = {
  fontSize: 12,
  letterSpacing: 2,
  textTransform: "uppercase" as const,
  color: "#0f4c81",
  fontWeight: 800,
} as const;

const heroTextStyle = {
  margin: 0,
  maxWidth: 960,
  lineHeight: 1.8,
  color: "#52667a",
} as const;

const summaryGridStyle = {
  display: "grid",
  gap: 12,
  gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
} as const;

const summaryCardStyle = {
  borderRadius: 20,
  padding: 16,
  background: "#ffffff",
  border: "1px solid rgba(148, 163, 184, 0.18)",
  boxShadow: "0 12px 24px rgba(15, 23, 42, 0.04)",
} as const;

const summaryLabelStyle = {
  color: "#64748b",
  fontSize: 13,
} as const;

const summaryValueStyle = {
  marginTop: 10,
  fontSize: 30,
  fontWeight: 800,
  color: "#102a43",
} as const;

const contentGridStyle = {
  display: "grid",
  gap: 18,
  gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
  alignItems: "start",
} as const;

const panelStyle = {
  background: "#ffffff",
  borderRadius: 24,
  padding: 20,
  border: "1px solid rgba(148, 163, 184, 0.18)",
  boxShadow: "0 16px 32px rgba(15, 23, 42, 0.05)",
} as const;

const sectionHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  alignItems: "flex-start",
  flexWrap: "wrap" as const,
} as const;

const sectionEyebrowStyle = {
  fontSize: 12,
  letterSpacing: 1.8,
  textTransform: "uppercase" as const,
  color: "#64748b",
  fontWeight: 800,
} as const;

const badgeStyle = {
  borderRadius: 999,
  padding: "6px 10px",
  background: "#f1f5f9",
  color: "#475569",
  fontSize: 12,
  fontWeight: 700,
} as const;

const quickGridStyle = {
  display: "grid",
  gap: 12,
  marginTop: 18,
} as const;

const quickCardStyle = {
  border: "1px solid rgba(148, 163, 184, 0.16)",
  borderRadius: 18,
  padding: 16,
  background: "#f8fafc",
  textAlign: "left" as const,
  cursor: "pointer",
} as const;

const quickDescStyle = {
  display: "block",
  marginTop: 8,
  color: "#5a6d7d",
  lineHeight: 1.7,
} as const;

const todoListStyle = {
  display: "grid",
  gap: 12,
  marginTop: 18,
  maxHeight: "46vh",
  overflowY: "auto" as const,
  paddingRight: 4,
} as const;

const workOrderListStyle = {
  display: "grid",
  gap: 12,
  marginTop: 18,
} as const;

const todoTopRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  alignItems: "flex-start",
  flexWrap: "wrap" as const,
} as const;

const todoMetaStyle = {
  marginTop: 8,
  color: "#64748b",
  lineHeight: 1.6,
  fontSize: 13,
} as const;

const todoSummaryStyle = {
  marginTop: 10,
  color: "#243b53",
  lineHeight: 1.7,
} as const;

const todoBottomRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  alignItems: "center",
  flexWrap: "wrap" as const,
  marginTop: 12,
} as const;

const todoInfoStyle = {
  display: "flex",
  gap: 12,
  flexWrap: "wrap" as const,
  color: "#64748b",
  fontSize: 13,
} as const;

const actionHintStyle = {
  color: "#0f4c81",
  fontSize: 13,
  fontWeight: 700,
} as const;

const statusPillStyle = {
  borderRadius: 999,
  padding: "6px 10px",
  background: "#e2e8f0",
  color: "#334155",
  fontSize: 12,
  fontWeight: 700,
} as const;

const workOrderCardStyle = {
  border: "1px solid rgba(148, 163, 184, 0.16)",
  borderRadius: 18,
  padding: 16,
  background: "#ffffff",
  textAlign: "left" as const,
  cursor: "pointer",
} as const;

const emptyStyle = {
  borderRadius: 18,
  padding: 16,
  background: "#f8fafc",
  border: "1px dashed rgba(148, 163, 184, 0.22)",
  color: "#64748b",
  lineHeight: 1.7,
} as const;
