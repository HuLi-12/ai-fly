# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

翼修通（Yixiutong）是面向航空制造与运维场景的智能排故协同 Agent MVP，采用 FastAPI + React 单项技术栈。

核心链路：故障输入 → 知识检索 → 排故推理 → 工单生成 → 人工确认 → 闭环反馈

## 常用命令

```bash
# 后端（从 yixiutong-mvp 根目录）
cd yixiutong-mvp && uvicorn apps.api.app.main:app --reload --port 8000

# 前端开发（从 apps/web）
cd yixiutong-mvp/apps/web && npm run dev

# 前端构建
cd yixiutong-mvp/apps/web && npm run build

# 测试
cd yixiutong-mvp && pytest -q

# 单测某文件
cd yixiutong-mvp && pytest tests/unit/test_diagnosis.py -v

# 一键启动（PowerShell）
./yixiutong-mvp/scripts/start_yixiutong.ps1
```

## 架构设计

### Agent 工作流（LangGraph）

`apps/api/app/agents/graph.py` 中定义了三节点状态机：

```
START → route → retrieve → diagnose → END
```

- **route**：根据故障码/描述判断场景类型（fault_diagnosis / process_deviation / quality_inspection）
- **retrieve**：从知识库检索证据片段 + 规则引擎评估风险等级
- **diagnose**：调用 LLM 生成诊断结果 + 工单草案

### Provider 模式

`apps/api/app/providers/factory.py` 实现 LLM 提供者工厂，支持双通道：
- **primary**：OpenAI-compatible 接口（云端大模型）
- **fallback**：本地 Ollama（yixiutong-qwen3b）

### 核心模块

| 模块 | 职责 |
|------|------|
| `app/agents/` | LangGraph 工作流、路由、诊断逻辑 |
| `app/services/` | 检索、摄取、通知、规则评估 |
| `app/repositories/` | 语料库、Portal 工单、反馈数据访问 |
| `app/api/v1/` | FastAPI 路由（auth、workflows、portal、knowledge 等） |

### 数据存储

- **SQLite**：`runtime/db/portal.sqlite3`（工单）、`runtime/db/feedback.sqlite3`（反馈）
- **知识索引**：`runtime/index/index.json`
- **风险规则**：`materials/rules/risk_rules.json`
- **配置**：`.env`（从 `.env.example` 复制）

## 目录结构

```
yixiutong-mvp/
├── apps/
│   ├── api/app/          # FastAPI 后端
│   └── web/              # React + Vite 前端
├── scripts/              # 启动脚本
├── tests/                # pytest 测试（api/ 和 unit/ 子目录）
├── .env.example
└── pyproject.toml
```

项目运行时依赖的 `materials/`、`runtime/`、`models/` 目录位于上级目录。

## 关键约定

- 工作目录：上游 .env 中 `PROJECT_ROOT` 指向的实际路径，代码中通过 `get_settings()` 获取
- 所有路径使用 `pathlib.Path`，跨平台兼容
- 前端无测试，后端测试使用 pytest + FastAPI TestClient
- 代码注释使用中文
