import { Fragment, type ReactNode } from "react";

type Props = {
  content: string;
};

function renderInline(text: string): ReactNode[] {
  const segments: ReactNode[] = [];
  const pattern = /(\[[^\]]+\]\((https?:\/\/[^\s)]+)\)|`[^`]+`)/g;
  let lastIndex = 0;

  for (const match of text.matchAll(pattern)) {
    const matched = match[0];
    const start = match.index ?? 0;
    if (start > lastIndex) {
      segments.push(text.slice(lastIndex, start));
    }

    if (matched.startsWith("[")) {
      const linkMatch = matched.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);
      if (linkMatch) {
        segments.push(
          <a key={`${start}-${matched}`} href={linkMatch[2]} target="_blank" rel="noreferrer" style={{ color: "#0d5c7d", fontWeight: 700 }}>
            {linkMatch[1]}
          </a>
        );
      } else {
        segments.push(matched);
      }
    } else {
      segments.push(
        <code
          key={`${start}-${matched}`}
          style={{
            padding: "2px 6px",
            borderRadius: 8,
            background: "rgba(9,52,84,0.08)",
            fontSize: "0.95em"
          }}
        >
          {matched.slice(1, -1)}
        </code>
      );
    }

    lastIndex = start + matched.length;
  }

  if (lastIndex < text.length) {
    segments.push(text.slice(lastIndex));
  }

  return segments.length ? segments : [text];
}

function renderTextBlock(line: string) {
  return (
    <Fragment>
      {renderInline(line).map((node, index) => (
        <Fragment key={index}>{node}</Fragment>
      ))}
    </Fragment>
  );
}

export function MarkdownArticle(props: Props) {
  const blocks = props.content
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);

  return (
    <article style={{ display: "grid", gap: 16 }}>
      {blocks.map((block, index) => {
        const lines = block
          .split("\n")
          .map((line) => line.trim())
          .filter(Boolean);
        if (!lines.length) {
          return null;
        }
        if (lines.every((line) => /^[-*]\s+/.test(line))) {
          return (
            <ul key={index} style={{ margin: 0, paddingLeft: 20, display: "grid", gap: 8 }}>
              {lines.map((line) => (
                <li key={line} style={{ lineHeight: 1.8 }}>
                  {renderTextBlock(line.replace(/^[-*]\s+/, ""))}
                </li>
              ))}
            </ul>
          );
        }
        if (lines.every((line) => /^\d+\.\s+/.test(line))) {
          return (
            <ol key={index} style={{ margin: 0, paddingLeft: 20, display: "grid", gap: 8 }}>
              {lines.map((line) => (
                <li key={line} style={{ lineHeight: 1.8 }}>
                  {renderTextBlock(line.replace(/^\d+\.\s+/, ""))}
                </li>
              ))}
            </ol>
          );
        }
        if (lines[0].startsWith("### ")) {
          return (
            <section key={index}>
              <h3 style={{ marginBottom: 10 }}>{lines[0].replace(/^###\s+/, "")}</h3>
              {lines.slice(1).map((line) => (
                <p key={line} style={{ marginTop: 0, marginBottom: 10, lineHeight: 1.8 }}>
                  {renderTextBlock(line)}
                </p>
              ))}
            </section>
          );
        }
        if (lines[0].startsWith("## ")) {
          return (
            <section key={index}>
              <h2 style={{ marginBottom: 10 }}>{lines[0].replace(/^##\s+/, "")}</h2>
              {lines.slice(1).map((line) => (
                <p key={line} style={{ marginTop: 0, marginBottom: 10, lineHeight: 1.8 }}>
                  {renderTextBlock(line)}
                </p>
              ))}
            </section>
          );
        }
        if (lines[0].startsWith("# ")) {
          return (
            <section key={index}>
              <h1 style={{ marginBottom: 10 }}>{lines[0].replace(/^#\s+/, "")}</h1>
              {lines.slice(1).map((line) => (
                <p key={line} style={{ marginTop: 0, marginBottom: 10, lineHeight: 1.8 }}>
                  {renderTextBlock(line)}
                </p>
              ))}
            </section>
          );
        }
        return (
          <p key={index} style={{ margin: 0, lineHeight: 1.9, color: "#22384d" }}>
            {renderTextBlock(lines.join(" "))}
          </p>
        );
      })}
    </article>
  );
}
