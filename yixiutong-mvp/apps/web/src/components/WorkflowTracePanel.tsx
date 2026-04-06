import type { AgentProgressItem, DiagnosisResponse, DiagnosisSessionState } from "../services/api";

type FinalTraceItem = NonNullable<DiagnosisResponse["execution_trace"]>[number];

type StageId = "route" | "retrieve" | "diagnose" | "work_order" | "respond";

type StageDefinition = {
  id: StageId;
  label: string;
  primaryNodes: string[];
  optionalNodes?: string[];
};

const stageDefinitions: StageDefinition[] = [
  { id: "route", label: "场景路由", primaryNodes: ["route"] },
  { id: "retrieve", label: "证据检索", primaryNodes: ["retrieve_primary"], optionalNodes: ["retrieve_retry"] },
  { id: "diagnose", label: "诊断研判", primaryNodes: ["diagnose", "trace", "score"], optionalNodes: ["second_opinion"] },
  { id: "work_order", label: "工单生成", primaryNodes: ["draft", "validate"], optionalNodes: ["repair_work_order"] },
  { id: "respond", label: "结果输出", primaryNodes: ["respond"] },
];

const statusMeta = {
  pending: { label: "等待中", color: "#64748b", soft: "#e2e8f0" },
  running: { label: "执行中", color: "#0f4c81", soft: "#dbeafe" },
  completed: { label: "已完成", color: "#2f855a", soft: "#dcfce7" },
  warning: { label: "需关注", color: "#b45309", soft: "#ffedd5" },
  retry: { label: "已重试", color: "#2563eb", soft: "#dbeafe" },
  fallback: { label: "兜底完成", color: "#c2410c", soft: "#ffedd5" },
  skipped: { label: "未触发", color: "#64748b", soft: "#f1f5f9" },
  failed: { label: "已失败", color: "#b91c1c", soft: "#fee2e2" },
} as const;

const finalStatuses = ["completed", "warning", "retry", "fallback", "skipped", "failed"] as const;

function toProgressItems(session: DiagnosisSessionState | null, executionTrace: FinalTraceItem[]): AgentProgressItem[] {
  if (session?.progress?.length) {
    return session.progress;
  }

  return executionTrace.map((item, index) => ({
    node: item.node,
    label: item.node,
    agent: item.agent ?? "Agent",
    status: item.status,
    summary: item.summary,
    detail: item.detail,
    updated_at: String(index),
  }));
}

function isFinalStatus(status: AgentProgressItem["status"]) {
  return finalStatuses.includes(status as (typeof finalStatuses)[number]);
}

function stageItems(items: AgentProgressItem[], definition: StageDefinition) {
  const allowedNodes = new Set([...(definition.primaryNodes ?? []), ...(definition.optionalNodes ?? [])]);
  return items.filter((item) => allowedNodes.has(item.node));
}

function isStageCompleted(items: AgentProgressItem[], definition: StageDefinition) {
  const primaryItems = items.filter((item) => definition.primaryNodes.includes(item.node));
  if (!primaryItems.length) {
    return false;
  }
  return primaryItems.every((item) => isFinalStatus(item.status));
}

function stageStatus(items: AgentProgressItem[], definition: StageDefinition): AgentProgressItem["status"] {
  const scopedItems = stageItems(items, definition);
  if (!scopedItems.length) {
    return "pending";
  }
  if (scopedItems.some((item) => item.status === "failed")) {
    return "failed";
  }
  if (scopedItems.some((item) => item.status === "running")) {
    return "running";
  }
  if (isStageCompleted(scopedItems, definition)) {
    if (scopedItems.some((item) => item.status === "warning")) {
      return "warning";
    }
    if (scopedItems.some((item) => item.status === "fallback")) {
      return "fallback";
    }
    if (scopedItems.some((item) => item.status === "retry")) {
      return "retry";
    }
    return "completed";
  }
  return "pending";
}

function currentStageIndex(session: DiagnosisSessionState | null, items: AgentProgressItem[]) {
  if (session?.current_node) {
    const explicitIndex = stageDefinitions.findIndex((definition) =>
      [...definition.primaryNodes, ...(definition.optionalNodes ?? [])].includes(session.current_node)
    );
    if (explicitIndex >= 0) {
      return explicitIndex;
    }
  }

  const runningIndex = stageDefinitions.findIndex((definition) => stageStatus(items, definition) === "running");
  if (runningIndex >= 0) {
    return runningIndex;
  }

  const lastCompletedIndex = [...stageDefinitions]
    .reverse()
    .findIndex((definition) => stageStatus(items, definition) !== "pending");
  if (lastCompletedIndex >= 0) {
    return stageDefinitions.length - lastCompletedIndex - 1;
  }

  return 0;
}

function progressPercent(session: DiagnosisSessionState | null, items: AgentProgressItem[]) {
  if (!stageDefinitions.length) {
    return 0;
  }
  if (session?.status === "completed") {
    return 100;
  }

  const completedCount = stageDefinitions.filter((definition) => {
    const status = stageStatus(items, definition);
    return status !== "pending" && status !== "running";
  }).length;
  const runningCount = stageDefinitions.filter((definition) => stageStatus(items, definition) === "running").length;
  const ratio = (completedCount + runningCount * 0.45) / stageDefinitions.length;
  return Math.max(4, Math.min(99, Math.round(ratio * 100)));
}

function currentAgent(session: DiagnosisSessionState | null, items: AgentProgressItem[], stageIndex: number) {
  if (session?.current_agent) {
    return session.current_agent;
  }
  const scopedItems = stageItems(items, stageDefinitions[stageIndex]);
  return scopedItems.find((item) => item.agent)?.agent ?? "Agent";
}

function currentSummary(session: DiagnosisSessionState | null, items: AgentProgressItem[], stageIndex: number) {
  const activeStage = stageDefinitions[stageIndex];
  const scopedItems = stageItems(items, activeStage);
  const runningItem = scopedItems.find((item) => item.status === "running");
  if (runningItem?.summary) {
    return runningItem.summary;
  }
  const finishedItem = [...scopedItems].reverse().find((item) => item.summary);
  if (finishedItem?.summary) {
    return finishedItem.summary;
  }
  if (session?.status === "completed") {
    return "本轮分析已完成，结果已写入诊断结论、工单草案和审批判断。";
  }
  return "系统会依次完成路由、检索、诊断、工单生成和结果输出，只在必要时触发二次检索、二次校正或工单修复。";
}

function buildBranchSummary(items: AgentProgressItem[]) {
  const pairs = [
    { node: "retrieve_retry", label: "二次检索" },
    { node: "second_opinion", label: "二次校正" },
    { node: "repair_work_order", label: "工单修复" },
  ] as const;

  return pairs.map((pair) => {
    const item = items.find((entry) => entry.node === pair.node);
    if (!item || item.status === "pending" || item.status === "skipped") {
      return `${pair.label}未触发`;
    }
    if (item.status === "running") {
      return `${pair.label}执行中`;
    }
    return `${pair.label}已触发`;
  });
}

export function WorkflowTracePanel(props: {
  session: DiagnosisSessionState | null;
  executionTrace: FinalTraceItem[];
  loading: boolean;
}) {
  const items = toProgressItems(props.session, props.executionTrace);
  const activeStageIndex = currentStageIndex(props.session, items);
  const activeStage = stageDefinitions[activeStageIndex];
  const percent = progressPercent(props.session, items);
  const branchSummary = buildBranchSummary(items);
  const stageAgent = currentAgent(props.session, items, activeStageIndex);
  const stageText = currentSummary(props.session, items, activeStageIndex);

  return (
    <section style={panelStyle}>
      <div style={headerStyle}>
        <div>
          <div style={eyebrowStyle}>Agent Progress</div>
          <h2 style={{ margin: "8px 0 8px" }}>分析进度</h2>
          <p style={descriptionStyle}>这里只保留用户最需要的进度信息：当前阶段、当前代理和本轮是否触发了额外分支。</p>
        </div>
        <div style={pillRowStyle}>
          <MetricPill label="当前阶段" value={activeStage.label} />
          <MetricPill label="当前代理" value={stageAgent} />
          <MetricPill label="完成度" value={`${percent}%`} strong />
        </div>
      </div>

      <div style={progressBlockStyle}>
        <div style={trackStyle}>
          <div style={{ ...fillStyle, width: `${percent}%` }} />
        </div>
        <div style={stageRowStyle}>
          {stageDefinitions.map((definition, index) => {
            const meta = statusMeta[stageStatus(items, definition)];
            const active = index === activeStageIndex;
            return (
              <div key={definition.id} style={stageItemStyle}>
                <span style={stageDotStyle(meta, active)} />
                <span style={{ ...stageLabelStyle, color: active ? "#102a43" : "#5f7285" }}>{definition.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div style={summaryCardStyle}>
        <div style={summaryTopRowStyle}>
          <strong style={{ color: "#102a43" }}>{activeStage.label}</strong>
          <span style={statePillStyle(statusMeta[stageStatus(items, activeStage)])}>
            {statusMeta[stageStatus(items, activeStage)].label}
          </span>
        </div>
        <div style={summaryTextStyle}>{stageText}</div>
        <div style={branchTextStyle}>{branchSummary.join(" · ")}</div>
      </div>

      {items.length ? (
        <details style={detailsStyle}>
          <summary style={detailsSummaryStyle}>查看详细步骤</summary>
          <div style={detailsListStyle}>
            {items.map((item) => (
              <div key={item.node} style={detailRowStyle}>
                <span style={detailNodeStyle}>{item.label}</span>
                <span style={detailAgentStyle}>{item.agent}</span>
                <span style={statePillStyle(statusMeta[item.status])}>{statusMeta[item.status].label}</span>
              </div>
            ))}
          </div>
        </details>
      ) : null}
    </section>
  );
}

function MetricPill(props: { label: string; value: string; strong?: boolean }) {
  return (
    <div style={metricPillStyle(props.strong)}>
      <div style={metricLabelStyle}>{props.label}</div>
      <strong style={{ color: props.strong ? "#ffffff" : "#102a43" }}>{props.value}</strong>
    </div>
  );
}

function metricPillStyle(strong = false) {
  return {
    minWidth: 120,
    borderRadius: 16,
    padding: "10px 12px",
    background: strong ? "#102a43" : "#f8fafc",
    border: `1px solid ${strong ? "rgba(15, 23, 42, 0.12)" : "rgba(148, 163, 184, 0.18)"}`,
  } as const;
}

function statePillStyle(meta: { label: string; color: string; soft: string }) {
  return {
    borderRadius: 999,
    padding: "6px 10px",
    background: meta.soft,
    color: meta.color,
    fontSize: 12,
    fontWeight: 700,
    flexShrink: 0,
  } as const;
}

function stageDotStyle(meta: { color: string; soft: string }, active: boolean) {
  return {
    width: 10,
    height: 10,
    borderRadius: "50%",
    background: meta.color,
    boxShadow: active ? `0 0 0 5px ${meta.soft}` : "none",
    transition: "box-shadow 160ms ease",
  } as const;
}

const panelStyle = {
  background: "#ffffff",
  borderRadius: 24,
  padding: 20,
  border: "1px solid rgba(148, 163, 184, 0.18)",
  boxShadow: "0 16px 36px rgba(15, 23, 42, 0.05)",
} as const;

const headerStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 16,
  alignItems: "flex-start",
  flexWrap: "wrap" as const,
} as const;

const eyebrowStyle = {
  fontSize: 12,
  letterSpacing: 2,
  textTransform: "uppercase" as const,
  color: "#0f4c81",
  fontWeight: 800,
} as const;

const descriptionStyle = {
  margin: 0,
  color: "#5f7285",
  lineHeight: 1.7,
  maxWidth: 780,
} as const;

const pillRowStyle = {
  display: "flex",
  gap: 10,
  flexWrap: "wrap" as const,
} as const;

const metricLabelStyle = {
  marginBottom: 6,
  fontSize: 12,
  color: "inherit",
  opacity: 0.74,
} as const;

const progressBlockStyle = {
  display: "grid",
  gap: 12,
  marginTop: 18,
} as const;

const trackStyle = {
  width: "100%",
  height: 8,
  borderRadius: 999,
  background: "#e2e8f0",
  overflow: "hidden" as const,
} as const;

const fillStyle = {
  height: "100%",
  borderRadius: 999,
  background: "linear-gradient(90deg, #0f4c81, #2f855a)",
  transition: "width 220ms ease",
} as const;

const stageRowStyle = {
  display: "grid",
  gap: 10,
  gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))",
} as const;

const stageItemStyle = {
  display: "flex",
  gap: 8,
  alignItems: "center",
} as const;

const stageLabelStyle = {
  fontSize: 13,
  fontWeight: 700,
} as const;

const summaryCardStyle = {
  marginTop: 16,
  borderRadius: 18,
  padding: 16,
  background: "#f8fafc",
  border: "1px solid rgba(148, 163, 184, 0.16)",
} as const;

const summaryTopRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 12,
  alignItems: "center",
  flexWrap: "wrap" as const,
} as const;

const summaryTextStyle = {
  marginTop: 10,
  color: "#243b53",
  lineHeight: 1.7,
} as const;

const branchTextStyle = {
  marginTop: 10,
  color: "#64748b",
  fontSize: 13,
  lineHeight: 1.6,
} as const;

const detailsStyle = {
  marginTop: 14,
  borderTop: "1px solid rgba(148, 163, 184, 0.16)",
  paddingTop: 12,
} as const;

const detailsSummaryStyle = {
  cursor: "pointer",
  color: "#0f4c81",
  fontWeight: 700,
} as const;

const detailsListStyle = {
  display: "grid",
  gap: 8,
  marginTop: 12,
} as const;

const detailRowStyle = {
  display: "grid",
  gridTemplateColumns: "minmax(110px, 1fr) minmax(130px, 1fr) auto",
  gap: 10,
  alignItems: "center",
  padding: "10px 12px",
  borderRadius: 14,
  background: "#ffffff",
  border: "1px solid rgba(148, 163, 184, 0.14)",
} as const;

const detailNodeStyle = {
  color: "#102a43",
  fontWeight: 700,
} as const;

const detailAgentStyle = {
  color: "#64748b",
  fontSize: 13,
} as const;
