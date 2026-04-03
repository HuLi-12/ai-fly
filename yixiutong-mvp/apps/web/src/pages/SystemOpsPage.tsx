import { SystemStatusPanel } from "../components/SystemStatusPanel";
import type { WorkspaceController } from "../hooks/useYixiutongWorkspace";

type Props = {
  workspace: WorkspaceController;
};

export function SystemOpsPage(props: Props) {
  return (
    <div style={{ display: "grid", gap: 20 }}>
      <section style={heroStyle}>
        <div style={{ fontSize: 12, letterSpacing: 2, textTransform: "uppercase", opacity: 0.76 }}>运行状态 / 主通道 / 部署</div>
        <h1 style={{ marginBottom: 10 }}>系统运维状态</h1>
        <p style={{ marginBottom: 0, maxWidth: 820, lineHeight: 1.7 }}>
          页面只保留演示和部署真正需要的配置状态，包括主通道、兜底通道、Ollama 就绪情况以及启动入口，不再展示实现阶段的磁盘守卫细节。
        </p>
      </section>

      <SystemStatusPanel selfCheck={props.workspace.selfCheck} providerChecks={props.workspace.providerChecks} />

      <section style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))" }}>
        <article style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>启动方式</h2>
          <div style={{ display: "grid", gap: 10 }}>
            {[
              "scripts/start_yixiutong.ps1",
              "scripts/start_yixiutong.cmd",
              "scripts/start_ollama.ps1",
              "scripts/register_ollama_model.ps1"
            ].map((command) => (
              <div key={command} style={commandStyle}>
                <code>{command}</code>
              </div>
            ))}
          </div>
        </article>

        <article style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>受控路径</h2>
          <div style={{ display: "grid", gap: 10 }}>
            {Object.entries(props.workspace.selfCheck?.controlled_roots ?? {}).slice(0, 6).map(([key, value]) => (
              <div key={key} style={pathRowStyle}>
                <strong>{key}</strong>
                <code style={{ display: "block", marginTop: 6, color: "#14405d", wordBreak: "break-all" }}>{value}</code>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}

const heroStyle = {
  borderRadius: 28,
  padding: 28,
  color: "#fff",
  background: "linear-gradient(125deg, rgba(53,33,79,0.98), rgba(66,77,130,0.92) 52%, rgba(28,108,143,0.88))"
} as const;

const panelStyle = {
  background: "rgba(255,255,255,0.92)",
  border: "1px solid rgba(9,52,84,0.1)",
  borderRadius: 24,
  padding: 20,
  boxShadow: "0 18px 40px rgba(20, 37, 55, 0.06)"
} as const;

const commandStyle = {
  padding: 12,
  borderRadius: 14,
  background: "#0f2333",
  color: "#e5f0f8"
} as const;

const pathRowStyle = {
  padding: 14,
  borderRadius: 16,
  background: "#f7fafc",
  border: "1px solid rgba(9,52,84,0.08)"
} as const;
