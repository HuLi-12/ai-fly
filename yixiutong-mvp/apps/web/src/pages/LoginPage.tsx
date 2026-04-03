import { useState } from "react";
import type { UserProfile } from "../services/api";

type Props = {
  demoUsers: UserProfile[];
  loading: boolean;
  onLogin: (username: string, password: string) => Promise<void>;
};

export function LoginPage(props: Props) {
  const [username, setUsername] = useState(props.demoUsers[0]?.username ?? "admin");
  const [password, setPassword] = useState("123456");

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: 24,
        background:
          "radial-gradient(circle at top left, rgba(31,112,160,0.24), transparent 32%), radial-gradient(circle at 85% 12%, rgba(44,155,118,0.18), transparent 26%), linear-gradient(180deg, #eef4f7 0%, #f8fbfc 46%, #eef4ef 100%)"
      }}
    >
      <div style={{ width: "min(1120px, 100%)", display: "grid", gap: 22, gridTemplateColumns: "1.1fr 0.9fr" }}>
        <section
          style={{
            borderRadius: 32,
            padding: 32,
            color: "#fff",
            background: "linear-gradient(130deg, rgba(8,32,60,0.98), rgba(8,88,121,0.94) 54%, rgba(39,146,122,0.88))",
            boxShadow: "0 24px 80px rgba(10, 32, 60, 0.24)"
          }}
        >
          <div style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: 2, opacity: 0.74 }}>OA 门户 / Agent 工作台</div>
          <h1 style={{ marginBottom: 12 }}>翼修通协同门户</h1>
          <p style={{ maxWidth: 620, lineHeight: 1.8 }}>
            这是一个围绕航空制造与运维场景构建的 OA 化 Agent 系统。它把智能排故、工艺偏差处置、质量隔离、审批待办、工单流转、知识资料库和消息插入统一到一个业务入口。
          </p>
          <div style={{ display: "grid", gap: 12, marginTop: 24 }}>
            {[
              "角色登录与权限导航",
              "待办审批箱与工单中心联动",
              "资料库在线查阅与案例检索",
              "企业微信 / 飞书消息通道插入"
            ].map((item) => (
              <div key={item} style={{ padding: 14, borderRadius: 18, background: "rgba(255,255,255,0.12)" }}>
                {item}
              </div>
            ))}
          </div>
        </section>

        <section
          style={{
            borderRadius: 28,
            padding: 28,
            background: "rgba(255,255,255,0.92)",
            border: "1px solid rgba(9,52,84,0.08)",
            boxShadow: "0 18px 40px rgba(20, 37, 55, 0.06)"
          }}
        >
          <h2 style={{ marginTop: 0 }}>登录系统</h2>
          <p style={{ color: "#5a6d7d", lineHeight: 1.7 }}>
            当前演示版提供内置角色账号。登录后会按照角色显示对应模块和待办。
          </p>
          <div style={{ display: "grid", gap: 12 }}>
            <label>
              <div style={{ marginBottom: 6 }}>用户名</div>
              <input value={username} onChange={(event) => setUsername(event.target.value)} style={fieldStyle} />
            </label>
            <label>
              <div style={{ marginBottom: 6 }}>密码</div>
              <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} style={fieldStyle} />
            </label>
          </div>
          <button type="button" onClick={() => void props.onLogin(username, password)} disabled={props.loading} style={loginButtonStyle}>
            {props.loading ? "登录中..." : "进入门户"}
          </button>

          <div style={{ marginTop: 22 }}>
            <h3 style={{ marginBottom: 12 }}>演示账号</h3>
            <div style={{ display: "grid", gap: 10 }}>
              {props.demoUsers.map((user) => (
                <button
                  key={user.user_id}
                  type="button"
                  onClick={() => {
                    setUsername(user.username);
                    setPassword("123456");
                  }}
                  style={{
                    border: "1px solid rgba(9,52,84,0.08)",
                    borderRadius: 16,
                    padding: 14,
                    background: "#f7fafc",
                    textAlign: "left",
                    cursor: "pointer"
                  }}
                >
                  <strong style={{ display: "block" }}>{user.display_name} / {user.role_label}</strong>
                  <span style={{ display: "block", marginTop: 6, color: "#5a6d7d" }}>
                    用户名：{user.username} | 默认密码：123456
                  </span>
                  <span style={{ display: "block", marginTop: 4, color: "#5a6d7d" }}>
                    {user.department} · {user.title}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

const fieldStyle = {
  width: "100%",
  borderRadius: 14,
  border: "1px solid rgba(12, 52, 83, 0.18)",
  padding: "12px 14px",
  fontSize: 14,
  boxSizing: "border-box" as const
};

const loginButtonStyle = {
  marginTop: 18,
  border: 0,
  borderRadius: 999,
  padding: "12px 18px",
  fontWeight: 700,
  cursor: "pointer",
  color: "#fff",
  background: "linear-gradient(135deg, #0d5c7d, #1a7f64)"
} as const;
