# 翼修通 MVP

翼修通当前已经不是单页 Demo，而是一套面向航空制造与运维场景的 OA 化 Agent 门户。它把智能排故、工艺偏差处置、质量隔离、待办审批、工单流转、资料库在线查阅、企业微信 / 飞书消息插入统一到了同一套前后端里。

## 当前能力

- 角色登录与门户导航
- 智能排故 / 工艺偏差 / 质量处置三类业务席位
- Agent 诊断结果自动生成工单
- 待办审批箱与工单中心联动
- 工单按待审批 / 待执行 / 处理中 / 已完成 / 驳回重审分组查看
- 在线资料库检索与正文查阅
- 官方参考资料解读与本地 PDF 归档
- 企业微信 / 飞书 Webhook 消息通道配置与测试
- 主通道 / 本地 Ollama 兜底通道状态检查

## 目录结构

- `apps/api`：FastAPI 后端、Agent 工作流、认证、门户接口
- `apps/web`：React + Vite OA 门户
- `scripts`：一键启动、索引构建、Ollama 注册、模型下载
- `tests`：API 与单元测试
- `../materials`：手册、案例、模板、比赛资料
- `../runtime`：索引、日志、缓存、SQLite
- `../models`：本地 Ollama / GGUF 模型存储

## 一键启动

直接运行：

- PowerShell：`scripts/start_yixiutong.ps1`
- 双击：`scripts/start_yixiutong.cmd`

启动后访问：

- 前端门户：`http://127.0.0.1:5173`
- 后端自检：`http://127.0.0.1:8000/api/v1/system/self-check`
- Provider 检查：`http://127.0.0.1:8000/api/v1/system/provider-check`

启动器会自动：

- 准备当前 D 盘目录下的运行缓存
- 调起 `D:/develop_tool/ollama/Ollama/ollama.exe`
- 打开后端窗口
- 打开前端窗口
- 等待前后端服务就绪

日志写入：

- `../runtime/logs/launcher`

## 门户模块

- `#/dashboard`：工作台总览
- `#/fault`：智能排故席位
- `#/process`：工艺偏差席位
- `#/quality`：质量处置席位
- `#/approvals`：待办审批箱
- `#/work_orders`：工单中心
- `#/knowledge`：资料库
- `#/notifications`：消息通道配置
- `#/ops`：系统状态

## 这版新增完善

- 待办审批默认只展示仍需处理的任务
- 已处理审批会沉淀到工单详情中的审批历史
- 工单中心支持多状态维度查看
- 资料中心新增 FAA 官方参考解读文档
- 工单页、审批页、资料页都加入了独立滚动区域

## 演示账号

默认密码均为 `123456`。

- `zhangwei`：维修工程师
- `liumin`：工艺工程师
- `wangyu`：质量工程师
- `chenhao`：审批主管
- `admin`：系统管理员

## 云端主通道配置

复制 `.env.example` 为 `.env`，设置：

- `PRIMARY_LLM_BASE_URL`
- `PRIMARY_LLM_API_KEY`
- `PRIMARY_LLM_MODEL`

后端按 OpenAI-compatible 接口调用主通道。

可用脚本验证配置：

- `scripts/validate_primary_provider.ps1`

验证报告写入：

- `../runtime/logs/primary_provider_validation.json`

已记录的官方接口验证结果（2026-04-03）：

- 目标：`https://api.openai.com/v1`
- 结果：`401 invalid_api_key`
- 因此仓库内 `.env` 仍保持 `PRIMARY_LLM_API_KEY=` 为空

## 本地 Ollama 兜底

当前项目已经支持本地兜底模型，经注册后的默认模型名为：

- `yixiutong-qwen3b`

关键脚本：

- `scripts/start_ollama.ps1`
- `scripts/register_ollama_model.ps1`
- `scripts/download_local_model.ps1`

默认本地模型来源：

- [Qwen/Qwen2.5-3B-Instruct-GGUF](https://hf.co/Qwen/Qwen2.5-3B-Instruct-GGUF)

当前显式 Ollama 可执行路径：

- `D:/develop_tool/ollama/Ollama/ollama.exe`

## 主要接口

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/demo-users`
- `POST /api/v1/diagnosis/start`
- `POST /api/v1/diagnosis/confirm`
- `POST /api/v1/feedback`
- `GET /api/v1/portal/overview`
- `GET /api/v1/portal/approvals`
  - 支持 `include_history=true`
- `GET /api/v1/portal/work-orders`
  - 支持 `status_bucket=pending_approval|pending_execution|in_progress|completed|rework`
- `GET /api/v1/portal/work-orders/{work_order_id}`
- `POST /api/v1/portal/work-orders/{work_order_id}/decision`
- `GET /api/v1/knowledge/documents`
- `GET /api/v1/knowledge/documents/{document_id}`
- `GET /api/v1/notifications/channels`
- `PUT /api/v1/notifications/channels/{channel}`
- `POST /api/v1/notifications/channels/{channel}/test`
- `GET /api/v1/system/self-check`
- `GET /api/v1/system/provider-check`

## 验证

后端测试：

- `pytest -q`

前端构建：

- `npm run build`

当前已验证通过（2026-04-03）：

- `pytest -q`：`20 passed`
- `npm run build`：成功
- OA 门户已完成登录、工单、审批、资料库、消息通道和系统状态联动

## 官方参考资料

已归档到 `../materials/knowledge/official_refs/raw` 的官方资料包括：

- `faa_amt_general_handbook.pdf`
- `faa_powerplant_ch10_engine_maintenance.pdf`
- `faa_ac_43_13_1b_change_1.pdf`

对应中文解读位于：

- `../materials/knowledge/official_refs`

## 说明

- 页面不再展示“磁盘空间守卫”这种实现期细节，只保留部署和演示真正需要看的系统状态
- 所有项目产物仍收口在当前 D 盘工作目录下
- 企业微信 / 飞书当前采用轻量 Webhook 直连，适合比赛演示与局域部署
