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

## 4. 当前待优化重点

| 优先级 | 状态 | 问题 | 建议方向 |
| --- | --- | --- | --- |
| P1 | `todo` | 路由仍偏规则化 | 升级为“规则 + 轻量分类器”双路由，返回 route confidence 和 route reason |
| P1 | `doing` | 检索已升级，但默认 embedding backend 仍是 hashing | 切换到真实 embedding provider 后重建索引 |
| P1 | `todo` | reranker 仍与诊断共享同一 LLM provider | 补独立 reranker 通道或独立 cross-encoder |
| P1 | `todo` | second opinion 还不是独立模型意见 | 升级为独立 provider 或独立 prompt 复核链路 |
| P1 | `todo` | 反馈未真正反哺 Agent | 建立案例记忆库，让已闭环工单成为高权重证据源 |
| P1 | `todo` | 置信度未校准 | 构建标准案例集，对阈值和权重做校准 |
| P1 | `todo` | 中文提示和文案仍有乱码遗留 | 做一次全链路中文清理 |
| P2 | `todo` | 缺少持久化工作流快照 | 对关键节点做持久化，支持审计和重放 |
| P2 | `todo` | 缺少 Agent 运行指标 | 增加 workflow metrics，记录耗时、成功率、重试率 |
| P2 | `todo` | 缺少标准评测集 | 建立 20 到 30 条标准案例集和固定评测脚本 |

## 5. 下一轮优先级

下一轮建议严格按下面顺序推进：

1. 先把 retrieval embedding provider 切到真实模型服务
2. 再补独立 reranker 通道
3. 然后做已闭环工单回灌为案例记忆库
4. 最后补路由解释和标准评测集

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
