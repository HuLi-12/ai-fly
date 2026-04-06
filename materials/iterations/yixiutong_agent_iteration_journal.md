# 翼修通 Agent 优化迭代总账

## 1. 文档用途

这份文档用于统一记录翼修通 Agent 的优化过程，后续每一次迭代都直接追加到本文档，不再新建零散总结文件。

本文档主要记录：

- 当前 Agent 基线能力
- 已完成的优化项
- 主动自检发现的问题
- 下一轮优先级和建议
- 每次迭代的验证结果

## 2. 当前 Agent 基线

截至 2026-04-05，当前 Agent 工作流为条件分支工作流：

`route -> retrieve_primary -> retrieve_retry(条件触发) -> diagnose -> trace -> score -> second_opinion(条件触发) -> draft_work_order -> validate -> repair_work_order(条件触发) -> respond`

当前已具备能力：

- 场景路由：故障诊断 / 工艺偏差 / 质量检验
- 混合检索：关键词 + 语义相似度 + rerank
- 证据追溯：建议到证据片段的映射
- 置信度评分：证据质量、追溯覆盖、provider 可靠性、风险修正
- 二次校正：低置信度时触发 second opinion
- 结构化工单：自动生成步骤、安全提示、审批要求
- 工单校验：不合格时自动 repair
- 审批策略：统一输出 `approval_reasons`
- 双通道 provider：主通道云 API，兜底本地 Ollama

## 3. 已完成优化

### 3.1 Agent 分支化与可解释性增强 `done`

已完成的改造包括：

- 将线性诊断流升级为条件分支工作流
- 新增低召回重试检索
- 新增低置信度 second opinion
- 新增工单校验失败后的 repair 分支
- 将审批判断统一收口到 `audit.py`
- 响应中新增 `approval_reasons`
- 增加 `traceability`、`confidence`、`validation_result`

### 3.2 真实混合检索第一阶段 `done`

已完成的改造包括：

- 新增 embedding 运行时
- 支持 `openai_compatible` embedding 接口
- 支持 `ollama` embedding 接口
- 未配置或失败时自动回退到本地 hashing embedding
- 索引写入 `embedding`、`embedding_backend`、`content_hash`
- 检索融合更新为“关键词召回 + 向量相似度 + 模型复排”
- 系统自检可以看到 retrieval 相关配置
- 证据返回 `retrieval_backend` 和 `model_rerank_score`
- 运行时索引已重建，当前后端为 `hashing`

### 3.3 基于体验分析的诊断工作台优化 `done`

本轮基于 `materials/iterations/EXPERIENCE_ANALYSIS.md` 做了筛选采纳，只接入当前代码库里低风险、高收益、且与 Agent 可解释性直接相关的建议。

已完成的改造包括：

- 输入面板补充字段级校验、场景示例和格式提示
- 新增草稿自动暂存、恢复草稿、清空草稿
- 错误提示改为可恢复的中文引导，而不是笼统报错
- 诊断页新增工作流执行轨迹面板，展示 route / retrieve / diagnose / validate 等节点状态
- 系统状态面板补充 retrieval provider、embedding model、模型复排状态
- 诊断链路相关页面做了一轮中文清理，移除关键路径乱码

本轮明确未采纳或暂缓的建议：

- `InputPanel` 为单一文本框输入：该判断已过期，当前项目本身已经是结构化输入
- 直接照搬 `sentence-transformers` 示例代码：不采纳，当前项目已进入可配置 embedding backend 路线
- MRB、NDT、完整趋势图、完整通知红点体系：暂缓，属于更大范围业务扩展，不适合插入本轮小步优化

### 3.4 案例记忆回灌与路由解释增强 `done`

本轮继续聚焦 Agent 本身，不扩散到整套 OA 流程重构，核心目标是让已闭环工单真正参与后续检索，同时让路由结果从“黑盒”变成结构化可解释输出。

已完成的改造包括：

- 路由升级为“规则评分 + 关键词信号 + 前缀判断”
- 响应新增 `route_confidence`、`route_reason`、`route_signals`
- 工作流 `route` 节点将路由依据写入执行轨迹
- 已闭环工单生成 `case_memory` 检索条目
- 检索层支持为动态案例记忆补 embedding，不依赖预构建索引
- 检索对 `case_memory` 增加适度权重提升，便于闭环经验回流
- 前端诊断面板补充路由解释展示
- 证据面板补充“闭环案例记忆”来源展示并清理关键乱码

### 3.5 Agent 实时分析过程可视化 `done`

本轮将 Agent 工作流从“结束后展示结果”升级为“分析中实时展示过程”，让前端可以直接看到当前正在执行的代理、当前步骤和每一步的阶段说明。

已完成的改造包括：

- 后端新增诊断会话机制，支持 `start-live` 与会话轮询
- 工作流节点在运行前后推送进度事件
- 每个节点补充代理标识，如 `Router Agent`、`Retrieval Agent`、`Diagnosis Agent`
- 前端改为使用 live session 方式发起诊断
- 诊断页新增实时过程面板，展示当前代理、步骤状态和阶段说明
- 过程展示从“多步骤卡片”收敛为“单一进度条 + 当前阶段说明”
- 诊断页输入区、复核区和过程区做了一轮视觉重排
- 最终响应与实时进度保持同一套工作流来源，避免前后端口径不一致

## 4. 当前待优化重点

| 优先级 | 状态 | 问题 | 建议方向 |
| --- | --- | --- | --- |
| P1 | `todo` | 路由仍偏规则化 | 升级为“规则 + 轻量分类器”双路由，返回 route confidence 和 route reason |
| P1 | `doing` | 检索已升级，但默认 embedding backend 仍是 hashing | 切换到真实 embedding provider 后重建索引 |
| P1 | `todo` | reranker 仍与诊断共享同一 LLM provider | 补独立 reranker 通道或独立 cross-encoder |
| P1 | `todo` | second opinion 还不是独立模型意见 | 升级为独立 provider 或独立 prompt 复核链路 |
| P1 | `done` | 反馈未真正反哺 Agent | 已建立基础案例记忆回灌，下一步提升权重策略和去重质量 |
| P1 | `todo` | 置信度未校准 | 构建标准案例集，对阈值和权重做校准 |
| P1 | `doing` | 中文提示和文案仍有乱码遗留 | 已清理诊断主链路，后续继续扩展到工单/门户页面 |
| P2 | `todo` | 缺少持久化工作流快照 | 对关键节点做持久化，支持审计和重放 |
| P2 | `todo` | 缺少 Agent 运行指标 | 增加 workflow metrics，记录耗时、成功率、重试率 |
| P2 | `todo` | 缺少标准评测集 | 建立 20 到 30 条标准案例集和固定评测脚本 |

## 5. 下一轮优先级

下一轮建议严格按下面顺序推进：

1. 先把 retrieval embedding provider 真正切到 Ollama 或云端 embedding 服务并重建索引
2. 再补独立 reranker 通道
3. 然后做案例记忆去重、权重校准和召回评估
4. 最后补标准评测集和路由/置信度校准

推荐参考组件：

- [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3)
- [BAAI/bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3)
- [Qwen/Qwen2.5-3B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF)

## 6. 迭代记录模板

后续每一轮 Agent 优化，直接按下面格式追加：

```md
## [迭代日期] 迭代主题

### 目标

- 

### 完成内容

- 

### 涉及代码

- 

### 验证结果

- 

### 新发现问题

- 

### 下一轮建议

- 
```

## 7. 当前迭代记录

### [2026-04-05] Agent 分支化与可解释性增强

- 工作流升级为条件分支图
- 新增低召回重试检索
- 新增低置信度 second opinion
- 新增工单校验失败后的 repair 分支
- 响应中新增 `approval_reasons`
- 验证结果：`pytest -q = 25 passed`，`npm run build` 通过

### [2026-04-05] 真实混合检索第一阶段

- 新增 embedding 运行时与 hashing fallback
- 索引写入 `embedding`、`embedding_backend`、`content_hash`
- 检索融合更新为“关键词召回 + 向量相似度 + 模型复排”
- 系统自检可查看 retrieval 配置状态
- 当前索引已重建成功，数量 `149 items`
- 当前 embedding backend：`hashing`
- 验证结果：定向测试 `6 passed`，后端全量测试 `27 passed`，前端构建通过

### [2026-04-05] 基于体验分析的诊断工作台优化

- 分析了 `materials/iterations/EXPERIENCE_ANALYSIS.md`，只采纳当前代码基线下有效且低风险的建议
- `InputPanel` 增加故障码格式校验、设备/现象必填校验、场景示例提示
- `useYixiutongWorkspace` 增加草稿自动保存、恢复草稿、错误类型中文化
- `DiagnosisPage` 新增动态操作引导和工作流执行轨迹展示
- `SystemStatusPanel` 新增检索后端状态展示
- 诊断关键路径组件完成一轮中文清理
- 明确忽略或后置过期/过大建议，如“单文本框输入”、“直接照搬 sentence-transformers 示例”、“完整 MRB/NDT 扩展”
- 验证结果：`npm run build` 通过

### [2026-04-05] 案例记忆回灌与路由解释增强

- 路由升级为“故障码前缀 + 中英文关键词 + 显式场景选择”联合判定
- 响应新增 `route_confidence`、`route_reason`、`route_signals`
- 已闭环工单会转成 `case_memory` 条目参与后续检索
- 检索层支持为动态案例记忆补 embedding，并对 `case_memory` 做适度加权
- 诊断页增加路由解释展示，证据页支持显示“闭环案例记忆”来源
- 验证结果：定向测试 `10 passed`，后端全量测试 `30 passed`，前端构建通过

### [2026-04-05] Agent 实时分析过程可视化

- 后端新增诊断会话接口：`/api/v1/diagnosis/start-live`、`/api/v1/diagnosis/sessions/{session_id}`
- 工作流节点支持推送 `running / completed / warning / retry / fallback` 状态
- 每个节点补充代理身份，前端可直接显示“当前由哪个 Agent 正在分析”
- 前端提交诊断后改为轮询 live session，并实时展示分析步骤
- `WorkflowTracePanel` 改为实时过程面板，不再只在结束后显示静态 trace
- 过程展示改为统一进度条，当前阶段和当前代理集中在单一信息面板中
- 验证结果：诊断会话测试 `4 passed`，后端全量测试 `31 passed`，前端构建通过

### [2026-04-05] 分析页布局与完成度语义修正

- 修正 live session 进度模型：可选分支未触发时改为 `skipped`，不再错误显示为“未完成”
- 二次检索、二次校正、工单修复现在会明确显示“已触发”或“未触发”
- 系统状态面板改为横向紧凑条，并收进折叠区域，减少对主流程的视觉干扰
- 证据回召、工单草案改为可折叠内容区，并增加各自独立滚动区
- 诊断页主视觉改为更克制的浅色卡片体系，降低高饱和渐变面积
- 关键流程文案统一修正为正常中文，提升“已完成度”和可信感

### [2026-04-06] 待办聚合与轻量进度展示

- 重新评估首页“最新待办”逻辑，确认原实现只展示审批任务，导致维修工程师场景下经常出现空列表
- 概览接口新增统一待办流 `latest_todos`，合并待审批、待执行、处理中和待跟踪任务
- 维修工程师在默认演示数据下会看到自己发起且仍待审批的工单跟踪项，不再误判为“没有待办”
- `WorkflowTracePanel` 从多块解释卡片收敛为轻量进度条，只保留当前阶段、当前代理、完成度和简要分支说明
- 详细步骤收进折叠明细，默认不干扰主操作区域
- 验证结果：门户接口测试与全量后端测试通过，前端构建通过

### [2026-04-06] Agent 运行时与可靠性治理第一阶段

- 新增 Prompt 系统化模块 `app/services/prompting.py`，按 `fault_diagnosis / process_deviation / quality_inspection` 三类场景统一角色设定、约束和 few-shot 示例
- 诊断生成链路改为“结构化提示优先，文本提示兜底，启发式诊断最后兜底”，实现位置在 `app/agents/diagnosis.py`
- 新增 `materials/rules/confidence_calibration.json` 与 `app/services/confidence_calibration.py`，把原始置信度改为“原始分 + 场景偏置 + provider 偏置 + 风险惩罚 + 证据/追溯惩罚”的校准分
- 工作流运行时新增 `AgentRuntimeRepository` 持久化运行记录、快照与节点耗时指标，支持按 `run_id` 和 `request_id` 做审计重放
- 新增结构化日志 `runtime/logs/agent_events.jsonl`，记录 workflow 启动、provider 调用、节点完成/失败、cache hit 等事件
- Provider 运行时补齐超时/瞬时错误重试与退避，`generate_text_with_fallback` / `generate_structured_with_fallback` 会先做同通道重试，再做主备降级
- 接口层新增：
- `GET /api/v1/diagnosis/runs/{run_id}`
- `GET /api/v1/diagnosis/replay/{request_id}`
- `GET /api/v1/diagnosis/metrics`
- `GET /api/v1/system/agent-metrics`
- 诊断请求新增幂等复用：相同请求命中 TTL 内已完成结果时，会直接返回缓存响应，但分配新的 `run_id`，并把该次请求记为 `cache_hit`
- live session 与普通诊断都已接入 `run_id`，后续可直接从前端诊断页跳到审计重放
- 验证结果：新增 runtime / retry / replay / idempotency 测试后，后端全量测试 `33 passed`

### [2026-04-06] 草稿保存与恢复流程重构

- 重新评估前端草稿链路，确认“切换场景”和“加载示例预设”原先共用一个动作，导致用户切场景时当前输入会被覆盖
- 新增独立 `changeScene` 流程：切换场景前会先同步保存当前场景的未保存输入，再按“本会话缓存 -> 已保存草稿 -> 预设模板”的优先级装载目标场景
- `restoreDraft` 改为真正的恢复动作，不再把恢复后的表单立刻再次标记为脏数据
- 自动保存改为延迟保存，减少每次键入都直接写本地存储的频率
- 草稿状态新增三类显式信号：`draftAvailable`、`draftDirty`、`draftSavedAt`
- 输入面板现在会直接展示“有未保存变更 / 已恢复草稿 / 当前内容已自动保存 / 当前为预设模板”这些状态，不再让用户猜测当前表单来源
- 模块切换从 `applyScenePreset` 改为 `changeScene`，不同业务席位之间切换时不会再无条件覆盖输入
- 验证结果：前端 `npm run build` 通过
