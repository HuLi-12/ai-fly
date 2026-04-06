import { useMemo } from "react";

import type { ProviderCheck, SelfCheckResponse } from "../services/api";
import { CollapsibleSection } from "./CollapsibleSection";

type CompactStatusItem = {
  title: string;
  value: string;
  tone: "ok" | "warn";
  detailRows: string[];
};

export function SystemStatusPanel(props: { selfCheck: SelfCheckResponse | null; providerChecks: ProviderCheck[] }) {
  const primary = props.providerChecks.find((item) => item.channel === "primary");
  const fallback = props.providerChecks.find((item) => item.channel === "fallback");

  const items = useMemo<CompactStatusItem[]>(
    () => [
      {
        title: "主通道",
        value: primary?.configured ? props.selfCheck?.provider || "已配置" : "未配置",
        tone: primary?.reachable ? "ok" : "warn",
        detailRows: [
          `连通性：${primary?.reachable ? "在线" : "未就绪"}`,
          `地址：${props.selfCheck?.primary_base_url || "未填写"}`,
          `说明：${primary?.detail || "等待检测"}`,
        ],
      },
      {
        title: "兜底通道",
        value: fallback?.configured ? props.selfCheck?.fallback_provider || "已配置" : "未配置",
        tone: fallback?.reachable ? "ok" : "warn",
        detailRows: [
          `连通性：${fallback?.reachable ? "在线" : "未就绪"}`,
          `地址：${props.selfCheck?.fallback_base_url || "未填写"}`,
          `说明：${fallback?.detail || "等待检测"}`,
        ],
      },
      {
        title: "本地模型",
        value: props.selfCheck?.local_model_present ? "已识别" : "未识别",
        tone: props.selfCheck?.local_model_present ? "ok" : "warn",
        detailRows: [
          `本地模式：${props.selfCheck?.local_model_enabled ? "开启" : "关闭"}`,
          `Ollama：${props.selfCheck?.ollama_executable_present ? "已识别" : "未识别"}`,
          `路径：${props.selfCheck?.ollama_executable_path || "未记录"}`,
        ],
      },
      {
        title: "检索后端",
        value: props.selfCheck?.retrieval_vector_enabled ? "向量检索已启用" : "关键词模式",
        tone: props.selfCheck?.retrieval_vector_enabled ? "ok" : "warn",
        detailRows: [
          `Embedding：${props.selfCheck?.retrieval_embedding_provider || "未配置"} / ${props.selfCheck?.retrieval_embedding_model || "未配置"}`,
          `模型复排：${props.selfCheck?.retrieval_model_rerank_enabled ? "已启用" : "未启用"}`,
          `缓存目录：${props.selfCheck?.cache_root || "未记录"}`,
        ],
      },
    ],
    [fallback, primary, props.selfCheck]
  );

  return (
    <CollapsibleSection
      title="系统状态"
      subtitle="只保留部署与运行真正需要关注的主通道、兜底通道、本地模型和检索状态。"
      badge={items.some((item) => item.tone === "warn") ? "有待完善" : "运行正常"}
      defaultOpen={false}
    >
      <div style={rowStyle}>
        {items.map((item) => (
          <article key={item.title} style={itemCardStyle(item.tone)}>
            <div style={itemHeadStyle}>
              <span style={itemTitleStyle}>{item.title}</span>
              <span style={statusDotStyle(item.tone)} />
            </div>
            <strong style={itemValueStyle}>{item.value}</strong>
            <div style={detailGridStyle}>
              {item.detailRows.map((row) => (
                <div key={row} style={detailRowStyle}>
                  {row}
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>
    </CollapsibleSection>
  );
}

const rowStyle = {
  display: "grid",
  gap: 12,
  gridTemplateColumns: "repeat(auto-fit, minmax(175px, 1fr))",
} as const;

const itemHeadStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 10,
  alignItems: "center",
} as const;

const itemTitleStyle = {
  fontSize: 12,
  letterSpacing: 1.2,
  textTransform: "uppercase" as const,
  color: "#486581",
  fontWeight: 800,
} as const;

const itemValueStyle = {
  display: "block",
  marginTop: 10,
  color: "#102a43",
  fontSize: 16,
  lineHeight: 1.4,
} as const;

const detailGridStyle = {
  display: "grid",
  gap: 6,
  marginTop: 12,
} as const;

const detailRowStyle = {
  color: "#5f7285",
  lineHeight: 1.55,
  fontSize: 12,
  wordBreak: "break-word" as const,
} as const;

function itemCardStyle(tone: "ok" | "warn") {
  return {
    borderRadius: 18,
    padding: 14,
    background: tone === "ok" ? "#f8fbfa" : "#fffbf6",
    border: `1px solid ${tone === "ok" ? "rgba(47, 133, 90, 0.14)" : "rgba(180, 83, 9, 0.18)"}`,
  } as const;
}

function statusDotStyle(tone: "ok" | "warn") {
  return {
    width: 10,
    height: 10,
    borderRadius: "50%",
    background: tone === "ok" ? "#2f855a" : "#d97706",
    boxShadow: `0 0 0 4px ${tone === "ok" ? "rgba(47,133,90,0.12)" : "rgba(217,119,6,0.14)"}`,
  } as const;
}
