# 翼修通 OA 门户自检报告

## 自检时间

- 日期：2026-04-03
- 范围：工单中心、待办审批、资料中心、滚动交互、公开资料补充

## 发现的问题

1. 工单中心只有单列表视角，缺少按阶段分组的能力。
2. 已审批完成的任务仍可能继续出现在“待办审批”语义里，待办和历史没有真正分层。
3. 工单详情信息过少，无法直接支撑演示“审批后如何执行、如何闭环”。
4. 资料中心内容偏少，且几乎全部来自项目自定义文本，缺少公开官方维修参考。
5. 资料中心更像文件列表，不像真正的知识库，标题与分类不够稳定。
6. 页面主要依赖整页滚动，工单列表、审批箱、资料阅读区缺少独立滚动体验。

## 已完成修复

### 工单中心

- 新增工单状态桶：
  - `pending_approval`
  - `pending_execution`
  - `in_progress`
  - `completed`
  - `rework`
- 工单页新增状态卡片和分栏切换。
- 工单详情页新增：
  - 异常描述
  - 最新说明
  - 建议处置步骤
  - 证据摘要
  - 审批历史
  - 最终结论

### 待办审批

- `/api/v1/portal/approvals` 默认只返回 `pending` 审批任务。
- 已通过 / 已驳回的审批不会继续出现在待办箱。
- 如需历史，可通过 `include_history=true` 获取。
- 审批页增加审批统计卡和审批历史展示。

### 状态流转

- 审批通过后，工单自动进入 `待执行` 状态桶。
- 只回填反馈但未给出最终结论时，工单进入 `处理中`。
- 填写最终结论后，工单进入 `已完成`。
- 审批驳回后，工单进入 `驳回重审`。

### 资料中心

- 新增 `官方参考` 分类。
- 知识服务改为优先从 Markdown 一级标题提取标题，而不是直接使用文件名。
- 新增 FAA 官方参考解读文档：
  - `faa_reference_catalog.md`
  - `faa_amt_general_handbook_digest.md`
  - `faa_powerplant_ch10_digest.md`
  - `ac_43_13_repair_digest.md`
  - `aviation_troubleshooting_playbook.md`
- 新增本地归档 PDF：
  - `faa_amt_general_handbook.pdf`
  - `faa_powerplant_ch10_engine_maintenance.pdf`
  - `faa_ac_43_13_1b_change_1.pdf`

### 页面交互

- 工单列表区加入独立滚动。
- 审批待办区加入独立滚动。
- 资料列表区和资料正文区加入独立滚动。
- Markdown 阅读组件新增外链与代码片段渲染支持。

## 本轮参考来源

- FAA 航空维修技术员手册总册
- FAA 发动机维护章节
- FAA AC 43.13-1B
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [ant-design-pro](https://github.com/ant-design/ant-design-pro)

## 当前仍可继续优化的点

1. 资料中心目前以中文解读和原始 PDF 归档为主，尚未做 PDF 在线预览。
2. 工单中心还没有“批量操作”和“按处理人 / 场景 / 风险”的组合筛选。
3. 审批页还没有单独的“已处理审批历史”页签。
4. 登录仍是演示账号模式，没有接企业统一认证。
5. 企业微信 / 飞书当前是 Webhook 直连，尚未扩展到应用级消息卡片。

## 验证结果

- `pytest -q`：20 passed
- `npm run build`：success
