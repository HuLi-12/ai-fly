import { useEffect, useState } from "react";
import { DashboardPage } from "./pages/DashboardPage";
import { DiagnosisPage } from "./pages/DiagnosisPage";
import { KnowledgeCenterPage } from "./pages/KnowledgeCenterPage";
import { LoginPage } from "./pages/LoginPage";
import { SystemOpsPage } from "./pages/SystemOpsPage";
import { ApprovalsPage } from "./pages/ApprovalsPage";
import { WorkOrdersPage } from "./pages/WorkOrdersPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { useYixiutongWorkspace, type PortalModule } from "./hooks/useYixiutongWorkspace";

const navMeta: Record<PortalModule, { label: string; subtitle: string }> = {
  dashboard: { label: "工作台", subtitle: "总览 / 快捷入口 / 最新待办" },
  fault: { label: "智能排故", subtitle: "异常诊断 / 工单生成 / 复核闭环" },
  process: { label: "工艺偏差", subtitle: "偏差分析 / 批次冻结 / 签审" },
  quality: { label: "质量处置", subtitle: "终检异常 / 隔离 / MRB 升级" },
  approvals: { label: "待办审批", subtitle: "审批箱 / 意见回写 / 流转" },
  work_orders: { label: "工单中心", subtitle: "列表 / 详情 / 状态跟踪" },
  knowledge: { label: "资料库", subtitle: "手册 / 案例 / 模板在线查阅" },
  notifications: { label: "消息配置", subtitle: "企业微信 / 飞书 Webhook" },
  ops: { label: "系统状态", subtitle: "主通道 / 本地模型 / 运行状态" }
};

const moduleTone = {
  fault: "linear-gradient(125deg, rgba(7,41,73,0.98), rgba(9,88,120,0.94) 52%, rgba(43,145,126,0.88))",
  process: "linear-gradient(125deg, rgba(80,53,16,0.98), rgba(155,105,36,0.92) 52%, rgba(204,150,68,0.86))",
  quality: "linear-gradient(125deg, rgba(84,26,54,0.98), rgba(145,54,84,0.92) 52%, rgba(191,89,114,0.86))"
} as const;

function routeFromHash(hash: string): PortalModule {
  const cleaned = hash.replace(/^#\/?/, "");
  if (cleaned in navMeta) {
    return cleaned as PortalModule;
  }
  return "dashboard";
}

export default function App() {
  const workspace = useYixiutongWorkspace();
  const [moduleKey, setModuleKey] = useState<PortalModule>(() => routeFromHash(window.location.hash));
  const [compact, setCompact] = useState(() => window.innerWidth < 1180);

  useEffect(() => {
    function syncRoute() {
      setModuleKey(routeFromHash(window.location.hash));
    }
    function syncViewport() {
      setCompact(window.innerWidth < 1180);
    }
    window.addEventListener("hashchange", syncRoute);
    window.addEventListener("resize", syncViewport);
    if (!window.location.hash) {
      window.history.replaceState(null, "", "#/dashboard");
    }
    return () => {
      window.removeEventListener("hashchange", syncRoute);
      window.removeEventListener("resize", syncViewport);
    };
  }, []);

  const allowedModules = new Set((workspace.user?.allowed_modules ?? []) as PortalModule[]);

  useEffect(() => {
    if (!workspace.user) {
      return;
    }
    if (!allowedModules.has(moduleKey)) {
      const first = workspace.user.allowed_modules[0] as PortalModule;
      window.location.hash = `#/${first}`;
    }
  }, [workspace.user, moduleKey]);

  useEffect(() => {
    if (moduleKey === "fault") {
      workspace.applyScenePreset("fault_diagnosis");
    }
    if (moduleKey === "process") {
      workspace.applyScenePreset("process_deviation");
    }
    if (moduleKey === "quality") {
      workspace.applyScenePreset("quality_inspection");
    }
  }, [moduleKey]);

  function navigate(module: PortalModule) {
    window.location.hash = `#/${module}`;
  }

  if (workspace.authLoading && !workspace.user) {
    return <div style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>系统加载中...</div>;
  }

  if (!workspace.user) {
    return <LoginPage demoUsers={workspace.demoUsers} loading={workspace.loginLoading} onLogin={workspace.loginAction} />;
  }

  const visibleNav = (workspace.user.allowed_modules as PortalModule[]).filter((item) => item in navMeta);
  const activeMeta = navMeta[moduleKey] ?? navMeta.dashboard;

  return (
    <main
      style={{
        minHeight: "100vh",
        background:
          "radial-gradient(circle at top left, rgba(35,123,173,0.18), transparent 34%), radial-gradient(circle at 85% 10%, rgba(62,173,122,0.18), transparent 26%), linear-gradient(180deg, #edf4f8 0%, #f6fafb 46%, #eef4ef 100%)",
        padding: compact ? 16 : 20,
        color: "#102f46",
        fontFamily: '"Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif'
      }}
    >
      <div style={{ maxWidth: 1520, margin: "0 auto", display: "grid", gap: 18, gridTemplateColumns: compact ? "1fr" : "280px minmax(0, 1fr)" }}>
        <aside
          style={{
            position: compact ? "static" : "sticky",
            top: 20,
            alignSelf: "start",
            borderRadius: 30,
            padding: 20,
            background: "linear-gradient(180deg, rgba(11,32,54,0.98), rgba(17,57,79,0.96))",
            color: "#fff",
            boxShadow: "0 24px 70px rgba(8, 28, 51, 0.24)"
          }}
        >
          <div style={{ paddingBottom: 20, borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
            <div style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: 2, opacity: 0.68 }}>航空业务门户</div>
            <h1 style={{ marginBottom: 8 }}>翼修通</h1>
            <p style={{ margin: 0, color: "rgba(255,255,255,0.74)", lineHeight: 1.7 }}>
              {workspace.user.display_name} · {workspace.user.role_label}
            </p>
            <p style={{ marginTop: 6, marginBottom: 0, color: "rgba(255,255,255,0.62)", lineHeight: 1.6 }}>
              {workspace.user.department}
            </p>
          </div>

          <nav style={{ display: "grid", gap: 10, marginTop: 18 }}>
            {visibleNav.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => navigate(item)}
                style={{
                  border: 0,
                  borderRadius: 18,
                  padding: 14,
                  textAlign: "left",
                  cursor: "pointer",
                  background: moduleKey === item ? "linear-gradient(135deg, rgba(255,255,255,0.18), rgba(69,173,150,0.28))" : "rgba(255,255,255,0.04)",
                  color: "#fff"
                }}
              >
                <strong style={{ display: "block", fontSize: 15 }}>{navMeta[item].label}</strong>
                <span style={{ display: "block", marginTop: 6, color: "rgba(255,255,255,0.72)", lineHeight: 1.5 }}>{navMeta[item].subtitle}</span>
              </button>
            ))}
          </nav>

          <button
            type="button"
            onClick={workspace.logoutAction}
            style={{
              marginTop: 18,
              width: "100%",
              border: "1px solid rgba(255,255,255,0.14)",
              borderRadius: 999,
              padding: "12px 18px",
              fontWeight: 700,
              cursor: "pointer",
              background: "rgba(255,255,255,0.06)",
              color: "#fff"
            }}
          >
            退出登录
          </button>
        </aside>

        <div style={{ display: "grid", gap: 18 }}>
          <header
            style={{
              borderRadius: 24,
              padding: "18px 22px",
              background: "rgba(255,255,255,0.82)",
              border: "1px solid rgba(9,52,84,0.08)",
              boxShadow: "0 18px 40px rgba(20, 37, 55, 0.04)"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 16, flexWrap: "wrap", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: 2, color: "#587286" }}>当前模块</div>
                <strong style={{ fontSize: 24 }}>{activeMeta.label}</strong>
                <div style={{ marginTop: 6, color: "#587286" }}>{activeMeta.subtitle}</div>
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                <HeaderChip label="当前角色" value={workspace.user.role_label} />
                <HeaderChip label="当前场景" value={workspace.scenePresets[workspace.sceneType].label} />
                <HeaderChip label="待审批数" value={String(workspace.overview?.summary.pending_approval_count ?? 0)} />
              </div>
            </div>
          </header>

          {workspace.error ? <MessageBanner tone="error" text={workspace.error} /> : null}
          {workspace.successMessage ? <MessageBanner tone="success" text={workspace.successMessage} /> : null}

          {moduleKey === "dashboard" ? <DashboardPage overview={workspace.overview} onOpenModule={navigate} onOpenWorkOrder={workspace.openWorkOrder} /> : null}
          {moduleKey === "fault" ? <DiagnosisPage title="智能排故席位" description="面向设备告警、维修排查与人工复核的协同业务席位。" moduleTone={moduleTone.fault} workspace={workspace} onOpenModule={navigate} /> : null}
          {moduleKey === "process" ? <DiagnosisPage title="工艺偏差席位" description="面向工艺参数偏移、批次冻结与工艺签审的协同席位。" moduleTone={moduleTone.process} workspace={workspace} onOpenModule={navigate} /> : null}
          {moduleKey === "quality" ? <DiagnosisPage title="质量处置席位" description="面向终检异常、隔离处置和 MRB 升级的协同席位。" moduleTone={moduleTone.quality} workspace={workspace} onOpenModule={navigate} /> : null}
          {moduleKey === "approvals" ? <ApprovalsPage workspace={workspace} /> : null}
          {moduleKey === "work_orders" ? <WorkOrdersPage workspace={workspace} /> : null}
          {moduleKey === "knowledge" ? <KnowledgeCenterPage workspace={workspace} /> : null}
          {moduleKey === "notifications" ? <NotificationsPage workspace={workspace} /> : null}
          {moduleKey === "ops" ? <SystemOpsPage workspace={workspace} /> : null}
        </div>
      </div>
    </main>
  );
}

function HeaderChip(props: { label: string; value: string }) {
  return (
    <div
      style={{
        minWidth: 160,
        padding: "10px 14px",
        borderRadius: 16,
        background: "#f5f8fb",
        border: "1px solid rgba(9,52,84,0.08)"
      }}
    >
      <div style={{ fontSize: 12, color: "#587286", textTransform: "uppercase", letterSpacing: 1 }}>{props.label}</div>
      <div style={{ marginTop: 6, fontWeight: 700 }}>{props.value}</div>
    </div>
  );
}

function MessageBanner(props: { tone: "success" | "error"; text: string }) {
  return (
    <section
      style={{
        borderRadius: 18,
        padding: "14px 16px",
        background: props.tone === "success" ? "#eefaf4" : "#fff2f1",
        border: `1px solid ${props.tone === "success" ? "rgba(20,108,67,0.14)" : "rgba(178,59,42,0.18)"}`,
        color: props.tone === "success" ? "#146c43" : "#b23b2a"
      }}
    >
      {props.text}
    </section>
  );
}
