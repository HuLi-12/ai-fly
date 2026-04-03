import type { PortalModule } from "../hooks/useYixiutongWorkspace";
import type { PortalOverviewResponse } from "../services/api";

type Props = {
  overview: PortalOverviewResponse | null;
  onOpenModule: (module: PortalModule) => void;
  onOpenWorkOrder: (workOrderId: string) => Promise<void>;
};

export function DashboardPage(props: Props) {
  const summary = props.overview?.summary;

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <section style={heroStyle}>
        <div style={{ fontSize: 12, letterSpacing: 2, textTransform: "uppercase", opacity: 0.72 }}>门户工作台</div>
        <h1 style={{ marginBottom: 10 }}>业务工作台</h1>
        <p style={{ marginBottom: 0, maxWidth: 900, lineHeight: 1.7 }}>
          工作台现在按业务状态来汇总待审批、待执行、处理中、已完成和驳回重审，不再只是页面入口。你可以从这里直接切入审批箱、工单中心和资料库。
        </p>
      </section>

      <section style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}>
        <StatCard title="工单总量" value={String(summary?.work_order_count ?? 0)} accent="linear-gradient(135deg, #0f5f85, #1d8a74)" />
        <StatCard title="待审批" value={String(summary?.pending_approval_count ?? 0)} accent="linear-gradient(135deg, #83590f, #c0842d)" />
        <StatCard title="待执行" value={String(summary?.pending_execution_count ?? 0)} accent="linear-gradient(135deg, #225f99, #4792cc)" />
        <StatCard title="处理中" value={String(summary?.in_progress_count ?? 0)} accent="linear-gradient(135deg, #4f3c83, #5c77ad)" />
        <StatCard title="已完成" value={String(summary?.completed_count ?? 0)} accent="linear-gradient(135deg, #3d6c47, #67a15c)" />
        <StatCard title="驳回重审" value={String(summary?.rework_count ?? 0)} accent="linear-gradient(135deg, #8c3827, #c75a46)" />
      </section>

      <section style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", alignItems: "start" }}>
        <article style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>快捷入口</h2>
          <div style={scrollAreaStyle}>
            {([
              { key: "fault", title: "发起智能排故", desc: "从异常告警直接进入 Agent 分析与工单生成。" },
              { key: "approvals", title: "处理待办审批", desc: "查看仍待处理的审批任务，已处理任务不再停留在待办箱。" },
              { key: "work_orders", title: "查看工单中心", desc: "按待审批、待执行、处理中、已完成等维度切换工单。" },
              { key: "knowledge", title: "查阅资料中心", desc: "在线查看项目手册、案例和 FAA 官方参考解读。" }
            ] as Array<{ key: PortalModule; title: string; desc: string }>).map((item) => (
              <button key={item.key} type="button" onClick={() => props.onOpenModule(item.key)} style={actionCardStyle}>
                <strong style={{ display: "block" }}>{item.title}</strong>
                <span style={{ display: "block", marginTop: 8, color: "#5a6d7d", lineHeight: 1.6 }}>{item.desc}</span>
              </button>
            ))}
          </div>
        </article>

        <article style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>最新待办</h2>
          <div style={scrollAreaStyle}>
            {props.overview?.approvals.length ? (
              props.overview.approvals.map((item) => (
                <button key={item.approval_id} type="button" onClick={() => props.onOpenModule("approvals")} style={approvalCardStyle}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                    <strong>{item.title}</strong>
                    <span style={approvalPillStyle}>{item.status_label}</span>
                  </div>
                  <div style={{ marginTop: 8, color: "#5a6d7d" }}>
                    {item.scene_label} / 指派给 {item.assignee_name} / {item.priority}优先级
                  </div>
                  <div style={{ marginTop: 8, color: "#5a6d7d", lineHeight: 1.6 }}>{item.comment}</div>
                </button>
              ))
            ) : (
              <p style={{ margin: 0, color: "#5a6d7d" }}>当前没有待办审批。</p>
            )}
          </div>
        </article>
      </section>

      <article style={panelStyle}>
        <h2 style={{ marginTop: 0 }}>最新工单</h2>
        <div style={scrollAreaStyle}>
          {props.overview?.work_orders.length ? (
            props.overview.work_orders.map((item) => (
              <button
                key={item.work_order_id}
                type="button"
                onClick={() => props.onOpenWorkOrder(item.work_order_id).then(() => props.onOpenModule("work_orders"))}
                style={workOrderCardStyle}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                  <strong>{item.title}</strong>
                  <span style={statusPillStyle(item.status_bucket_label)}>{item.status_bucket_label}</span>
                </div>
                <div style={{ marginTop: 8, color: "#5a6d7d", lineHeight: 1.6 }}>{item.summary}</div>
                <div style={{ marginTop: 10, color: "#5a6d7d" }}>
                  {item.scene_label} / {item.priority}优先级 / 处理席位 {item.assignee_name}
                </div>
              </button>
            ))
          ) : (
            <p style={{ margin: 0, color: "#5a6d7d" }}>尚未生成工单。你可以先从业务席位发起一次 Agent 分析。</p>
          )}
        </div>
      </article>
    </div>
  );
}

function StatCard(props: { title: string; value: string; accent: string }) {
  return (
    <article style={{ borderRadius: 22, padding: 18, color: "#fff", background: props.accent }}>
      <div style={{ fontSize: 13, letterSpacing: 1, opacity: 0.8 }}>{props.title}</div>
      <div style={{ marginTop: 12, fontSize: 32, fontWeight: 800 }}>{props.value}</div>
    </article>
  );
}

function statusPillStyle(label: string) {
  return {
    borderRadius: 999,
    padding: "6px 10px",
    background: "#eef4ef",
    color: "#2e5d37",
    fontWeight: 700,
    fontSize: 12
  } as const;
}

const heroStyle = {
  borderRadius: 28,
  padding: 28,
  color: "#fff",
  background: "linear-gradient(125deg, rgba(10,35,63,0.98), rgba(8,102,132,0.92) 55%, rgba(36,142,106,0.88))",
  boxShadow: "0 24px 70px rgba(8, 35, 63, 0.22)"
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
  maxHeight: "48vh",
  overflowY: "auto" as const,
  paddingRight: 4
};

const actionCardStyle = {
  border: "1px solid rgba(9,52,84,0.08)",
  borderRadius: 18,
  padding: 16,
  background: "#f7fafc",
  textAlign: "left" as const,
  cursor: "pointer"
};

const approvalCardStyle = {
  border: "1px solid rgba(9,52,84,0.08)",
  borderRadius: 18,
  padding: 16,
  background: "#fff8ef",
  textAlign: "left" as const,
  cursor: "pointer"
};

const workOrderCardStyle = {
  border: "1px solid rgba(9,52,84,0.08)",
  borderRadius: 18,
  padding: 16,
  background: "#f7fafc",
  textAlign: "left" as const,
  cursor: "pointer"
};

const approvalPillStyle = {
  borderRadius: 999,
  padding: "6px 10px",
  background: "#fff1d6",
  color: "#9a6200",
  fontWeight: 700,
  fontSize: 12
} as const;
