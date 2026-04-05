# Implementation Tasks

## Phase 1: 已完成

- [x] 重写增强规格文档，明确一阶段与二阶段边界
- [x] 将检索升级为混合检索，并输出关键词分、语义分、重排分和最终分
- [x] 为诊断结果增加证据追溯映射
- [x] 增加置信度评分、告警信息和人工复核判定
- [x] 将工单草案升级为模板化结构，并加入校验结果
- [x] 将 LangGraph 工作流升级为带分支的流程
- [x] 增加低召回二次检索
- [x] 增加低置信度二次校正
- [x] 增加统一审批策略与审批理由输出
- [x] 更新诊断页以展示新增字段
- [x] 补充单元测试与 API 测试

## Current Workflow

```text
route
  -> retrieve_primary
  -> low recall ? retrieve_retry : diagnose
  -> trace
  -> score
  -> low confidence ? second_opinion : draft_work_order
  -> validate
  -> invalid ? repair_work_order : respond
```

## Phase 2: 待实现

- [ ] 接入真实 embedding 检索索引
- [ ] 接入真实 reranker（如 BGE-reranker-v2-m3）
- [ ] 构建标准化测试案例集
- [ ] 建立自动化评测报告
- [ ] 将闭环工单反馈回灌到知识检索
- [ ] 将 execution trace 展示扩展到门户更多页面
- [ ] 清理其余历史乱码文案

## Validation Status

- [x] `pytest -q`
- [x] `npm run build`

## Notes

当前版本优先保证“可运行、可解释、可审批、可演示”。

性能压测、评测引擎和重型模型接入保留为二阶段，不在本轮实现范围内。
