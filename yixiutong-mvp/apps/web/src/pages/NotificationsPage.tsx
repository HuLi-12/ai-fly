import { useState } from "react";
import type { NotificationChannel } from "../services/api";
import type { WorkspaceController } from "../hooks/useYixiutongWorkspace";

type Props = {
  workspace: WorkspaceController;
};

export function NotificationsPage(props: Props) {
  return (
    <div style={{ display: "grid", gap: 20 }}>
      <section style={heroStyle}>
        <div style={{ fontSize: 12, letterSpacing: 2, textTransform: "uppercase", opacity: 0.76 }}>消息集成</div>
        <h1 style={{ marginBottom: 10 }}>企业微信 / 飞书消息插入</h1>
        <p style={{ marginBottom: 0, maxWidth: 820, lineHeight: 1.7 }}>
          当前实现使用 Webhook 直连，适合比赛演示和轻量部署。你可以把高风险工单或审批待办推送到企业微信群或飞书群。
        </p>
      </section>

      <div style={{ display: "grid", gap: 16 }}>
        {props.workspace.notificationChannels.map((channel) => (
          <NotificationCard key={channel.channel} channel={channel} workspace={props.workspace} />
        ))}
      </div>
    </div>
  );
}

function NotificationCard(props: { channel: NotificationChannel; workspace: WorkspaceController }) {
  const [enabled, setEnabled] = useState(props.channel.enabled);
  const [webhookUrl, setWebhookUrl] = useState(props.channel.webhook_url);
  const [secret, setSecret] = useState(props.channel.secret);
  const [receiverHint, setReceiverHint] = useState(props.channel.receiver_hint);

  return (
    <article style={panelStyle}>
      <h2 style={{ marginTop: 0 }}>{props.channel.display_name}</h2>
      <div style={{ display: "grid", gap: 12 }}>
        <label>
          <div style={{ marginBottom: 6 }}>启用状态</div>
          <select value={enabled ? "enabled" : "disabled"} onChange={(event) => setEnabled(event.target.value === "enabled")} style={fieldStyle}>
            <option value="enabled">启用</option>
            <option value="disabled">停用</option>
          </select>
        </label>
        <label>
          <div style={{ marginBottom: 6 }}>Webhook 地址</div>
          <input value={webhookUrl} onChange={(event) => setWebhookUrl(event.target.value)} placeholder="填写企业微信或飞书机器人的 webhook 地址" style={fieldStyle} />
        </label>
        <label>
          <div style={{ marginBottom: 6 }}>签名密钥（可选）</div>
          <input value={secret} onChange={(event) => setSecret(event.target.value)} placeholder="需要时填写，当前轻量实现默认走 webhook 直连" style={fieldStyle} />
        </label>
        <label>
          <div style={{ marginBottom: 6 }}>接收方说明</div>
          <input value={receiverHint} onChange={(event) => setReceiverHint(event.target.value)} placeholder="例如：维修群 / 工艺群 / 质量群" style={fieldStyle} />
        </label>
      </div>

      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 16 }}>
        <button
          type="button"
          onClick={() => void props.workspace.saveNotificationChannel(props.channel.channel, { enabled, webhook_url: webhookUrl, secret, receiver_hint: receiverHint })}
          disabled={props.workspace.notificationSaving}
          style={saveButtonStyle}
        >
          保存配置
        </button>
        <button
          type="button"
          onClick={() => void props.workspace.runNotificationTest(props.channel.channel, { title: "翼修通测试消息", content: "当前消息通道已接入，可用于工单提醒与审批通知。" })}
          disabled={props.workspace.notificationSaving}
          style={testButtonStyle}
        >
          发送测试消息
        </button>
      </div>

      <div style={{ display: "grid", gap: 6, marginTop: 16, color: "#5a6d7d" }}>
        <div>最近状态：{props.channel.last_status}</div>
        <div>最近说明：{props.channel.last_message || "暂无记录"}</div>
        <div>更新时间：{props.channel.updated_at}</div>
      </div>
    </article>
  );
}

const heroStyle = {
  borderRadius: 28,
  padding: 28,
  color: "#fff",
  background: "linear-gradient(125deg, rgba(78,27,68,0.98), rgba(127,53,120,0.92) 54%, rgba(97,97,178,0.86))"
} as const;

const panelStyle = {
  background: "rgba(255,255,255,0.92)",
  border: "1px solid rgba(9,52,84,0.1)",
  borderRadius: 24,
  padding: 20,
  boxShadow: "0 18px 40px rgba(20, 37, 55, 0.06)"
} as const;

const fieldStyle = {
  width: "100%",
  borderRadius: 12,
  border: "1px solid rgba(12, 52, 83, 0.18)",
  padding: "12px 14px",
  fontSize: 14,
  boxSizing: "border-box" as const
};

const saveButtonStyle = {
  border: 0,
  borderRadius: 999,
  padding: "12px 18px",
  fontWeight: 700,
  cursor: "pointer",
  color: "#fff",
  background: "linear-gradient(135deg, #0d5c7d, #1a7f64)"
} as const;

const testButtonStyle = {
  border: "1px solid rgba(9,52,84,0.12)",
  borderRadius: 999,
  padding: "12px 18px",
  fontWeight: 700,
  cursor: "pointer",
  background: "#fff",
  color: "#14344a"
} as const;
