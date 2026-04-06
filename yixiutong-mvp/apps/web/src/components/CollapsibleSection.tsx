import { useState, type CSSProperties, type ReactNode } from "react";

export function CollapsibleSection(props: {
  title: string;
  subtitle?: string;
  badge?: string;
  defaultOpen?: boolean;
  children: ReactNode;
  bodyStyle?: CSSProperties;
}) {
  const [open, setOpen] = useState(Boolean(props.defaultOpen));

  return (
    <section style={shellStyle}>
      <button type="button" onClick={() => setOpen((current) => !current)} style={headerButtonStyle}>
        <div style={{ minWidth: 0 }}>
          <div style={titleRowStyle}>
            <strong style={titleStyle}>{props.title}</strong>
            {props.badge ? <span style={badgeStyle}>{props.badge}</span> : null}
          </div>
          {props.subtitle ? <p style={subtitleStyle}>{props.subtitle}</p> : null}
        </div>
        <span style={chevronStyle(open)}>{open ? "收起" : "展开"}</span>
      </button>

      {open ? <div style={{ ...bodyBaseStyle, ...props.bodyStyle }}>{props.children}</div> : null}
    </section>
  );
}

const shellStyle = {
  borderRadius: 22,
  border: "1px solid rgba(148, 163, 184, 0.22)",
  background: "#ffffff",
  boxShadow: "0 12px 28px rgba(15, 23, 42, 0.05)",
} as const;

const headerButtonStyle = {
  width: "100%",
  border: 0,
  background: "transparent",
  padding: "18px 18px 16px",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  gap: 16,
  cursor: "pointer",
  textAlign: "left" as const,
} as const;

const titleRowStyle = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  flexWrap: "wrap" as const,
} as const;

const titleStyle = {
  fontSize: 18,
  color: "#102a43",
} as const;

const badgeStyle = {
  padding: "4px 10px",
  borderRadius: 999,
  background: "#eef2f7",
  color: "#486581",
  fontSize: 12,
  fontWeight: 700,
} as const;

const subtitleStyle = {
  margin: "8px 0 0",
  color: "#52667a",
  lineHeight: 1.7,
  fontSize: 13,
} as const;

const bodyBaseStyle = {
  padding: "0 18px 18px",
} as const;

function chevronStyle(open: boolean) {
  return {
    flexShrink: 0,
    borderRadius: 999,
    padding: "7px 11px",
    background: open ? "#102a43" : "#f8fafc",
    color: open ? "#ffffff" : "#486581",
    fontSize: 12,
    fontWeight: 700,
    transition: "all 160ms ease",
  } as const;
}
