# 本地 3B 模型部署说明

1. 在 `.env` 中设置 `LOCAL_MODEL_ENABLED=true`。
2. 如果下载模型需要鉴权，填写 `HF_TOKEN`。
3. 在 `yixiutong-mvp` 目录运行 `scripts/download_local_model.ps1`。
4. 确认 `models/local-llm/download_manifest.json` 已生成。
5. 如果使用 Ollama 作为运行时，再执行 `scripts/register_ollama_model.ps1`。
6. 保持 `FALLBACK_LLM_MODEL=yixiutong-qwen3b`，并通过 `scripts/start_ollama.ps1` 启动服务。

## 当前约定

- 本地兜底模型用于比赛演示与离线可用性保障。
- 主通道优先使用已配置的 OpenAI-compatible 服务。
- 所有模型文件和缓存都固定在当前 D 盘项目目录内。
