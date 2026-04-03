# Cloud Provider Setup

1. Set `PRIMARY_LLM_PROVIDER=openai_compatible`.
2. Fill `PRIMARY_LLM_BASE_URL` with the cloud inference endpoint.
3. Fill `PRIMARY_LLM_API_KEY` with the access token.
4. Keep `PRIMARY_LLM_MODEL` aligned with the deployed model name.
5. Call `/api/v1/system/provider-check` to verify reachability before the demo.

## Validation record

- Validation helper: `yixiutong-mvp/scripts/validate_primary_provider.ps1`
- Output report: `runtime/logs/primary_provider_validation.json`
- Recorded on `2026-04-03` against `https://api.openai.com/v1`
- Masked credential preview: `sk-e75...c694`
- Result: `401 invalid_api_key`

The repository `.env` deliberately leaves `PRIMARY_LLM_API_KEY=` blank. Add a valid key or the correct third-party OpenAI-compatible base URL before enabling the primary channel.
