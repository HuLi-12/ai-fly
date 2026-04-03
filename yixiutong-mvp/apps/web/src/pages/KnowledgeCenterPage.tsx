import { useState } from "react";
import { MarkdownArticle } from "../components/MarkdownArticle";
import type { WorkspaceController } from "../hooks/useYixiutongWorkspace";

type Props = {
  workspace: WorkspaceController;
};

export function KnowledgeCenterPage(props: Props) {
  const { workspace } = props;
  const [keyword, setKeyword] = useState("");
  const [category, setCategory] = useState("");

  const categories = Array.from(new Set(workspace.knowledgeDocuments.map((item) => item.category))).sort((a, b) =>
    a.localeCompare(b, "zh-CN")
  );

  async function search(nextCategory = category) {
    await workspace.loadKnowledgeDocuments({ keyword: keyword || undefined, category: nextCategory || undefined });
  }

  return (
    <div style={{ display: "grid", gap: 20 }}>
      <section style={heroStyle}>
        <div style={{ fontSize: 12, letterSpacing: 2, textTransform: "uppercase", opacity: 0.76 }}>资料知识库</div>
        <h1 style={{ marginBottom: 10 }}>资料中心在线查阅</h1>
        <p style={{ marginBottom: 0, maxWidth: 900, lineHeight: 1.7 }}>
          资料中心现在不仅有本项目自定义手册，也加入了可公开引用的官方维修参考解读。左侧做文档检索和分类筛选，右侧直接在线阅读正文。
        </p>
      </section>

      <div style={{ display: "grid", gap: 20, gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", alignItems: "start" }}>
        <article style={panelStyle}>
          <div style={{ display: "grid", gap: 10 }}>
            <input
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="按标题、摘要或路径搜索资料"
              style={inputStyle}
            />
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <CategoryButton
                active={category === ""}
                label="全部"
                onClick={async () => {
                  setCategory("");
                  await workspace.loadKnowledgeDocuments({ keyword: keyword || undefined });
                }}
              />
              {categories.map((item) => (
                <CategoryButton
                  key={item}
                  active={category === item}
                  label={item}
                  onClick={async () => {
                    setCategory(item);
                    await search(item);
                  }}
                />
              ))}
            </div>
            <button type="button" onClick={() => void search()} style={searchButtonStyle}>
              刷新资料列表
            </button>
          </div>

          <div style={scrollAreaStyle}>
            {workspace.knowledgeDocuments.map((doc) => (
              <button
                key={doc.document_id}
                type="button"
                onClick={() => void workspace.openDocument(doc.document_id)}
                style={{
                  ...docCardStyle,
                  borderColor:
                    workspace.selectedDocument?.document_id === doc.document_id ? "rgba(41,78,32,0.38)" : "rgba(9,52,84,0.08)",
                  background: workspace.selectedDocument?.document_id === doc.document_id ? "#eef6ec" : "#f7fafc"
                }}
              >
                <strong style={{ display: "block" }}>{doc.title}</strong>
                <span style={{ display: "block", marginTop: 6, color: "#5a6d7d" }}>
                  {doc.category} / {doc.scene_type} / {doc.updated_at}
                </span>
                <span style={{ display: "block", marginTop: 8, color: "#5a6d7d", lineHeight: 1.6 }}>{doc.summary}</span>
              </button>
            ))}
            {!workspace.knowledgeDocuments.length ? <p style={{ margin: 0, color: "#5a6d7d" }}>没有匹配到资料。</p> : null}
          </div>
        </article>

        <article style={panelStyle}>
          {workspace.selectedDocument ? (
            <div style={scrollAreaStyle}>
              <section>
                <h2 style={{ marginTop: 0, marginBottom: 8 }}>{workspace.selectedDocument.title}</h2>
                <div style={{ color: "#5a6d7d", lineHeight: 1.7 }}>
                  {workspace.selectedDocument.category} / {workspace.selectedDocument.scene_type}
                </div>
                <div style={{ marginTop: 6, color: "#5a6d7d", lineHeight: 1.7 }}>{workspace.selectedDocument.relative_path}</div>
              </section>
              <MarkdownArticle content={workspace.selectedDocument.content} />
            </div>
          ) : (
            <p style={{ margin: 0, color: "#5a6d7d" }}>请选择左侧资料查看正文。</p>
          )}
        </article>
      </div>
    </div>
  );
}

function CategoryButton(props: { label: string; active: boolean; onClick: () => void | Promise<void> }) {
  return (
    <button
      type="button"
      onClick={() => void props.onClick()}
      style={{
        border: "1px solid rgba(9,52,84,0.08)",
        borderRadius: 999,
        padding: "9px 14px",
        cursor: "pointer",
        fontWeight: 700,
        background: props.active ? "linear-gradient(135deg, #365f29, #5f8f48)" : "#fff",
        color: props.active ? "#fff" : "#23445c"
      }}
    >
      {props.label}
    </button>
  );
}

const heroStyle = {
  borderRadius: 28,
  padding: 28,
  color: "#fff",
  background: "linear-gradient(125deg, rgba(41,78,32,0.98), rgba(72,120,71,0.92) 54%, rgba(151,176,111,0.86))"
} as const;

const panelStyle = {
  background: "rgba(255,255,255,0.92)",
  border: "1px solid rgba(9,52,84,0.1)",
  borderRadius: 24,
  padding: 20,
  boxShadow: "0 18px 40px rgba(20, 37, 55, 0.06)"
} as const;

const inputStyle = {
  width: "100%",
  borderRadius: 14,
  border: "1px solid rgba(9,52,84,0.12)",
  padding: "12px 14px"
} as const;

const searchButtonStyle = {
  border: 0,
  borderRadius: 999,
  padding: "12px 18px",
  fontWeight: 700,
  cursor: "pointer",
  color: "#fff",
  background: "linear-gradient(135deg, #365f29, #5f8f48)"
} as const;

const scrollAreaStyle = {
  display: "grid",
  gap: 12,
  marginTop: 18,
  maxHeight: "68vh",
  overflowY: "auto" as const,
  paddingRight: 4
};

const docCardStyle = {
  border: "1px solid rgba(9,52,84,0.08)",
  borderRadius: 18,
  padding: 16,
  background: "#f7fafc",
  textAlign: "left" as const,
  cursor: "pointer"
};
