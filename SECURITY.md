# Security Policy / 安全说明

请不要把 API Key、私有模型、未公开论文或私人数据提交到仓库。

This open release removed the original license gate and launch guard. If you discover a security issue, please open a private report with reproduction steps and affected files.

Known intentional network behavior:

- `main.py` checks `http://localhost:<port>/_stcore/health` to wait for Streamlit.
- `api/llm_client.py` can call a user-configured OpenAI-compatible API endpoint.
- No remote telemetry endpoint is configured by this project.
