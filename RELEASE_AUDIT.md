# Release Audit / 发布清理审计

## 中文

本次开源整理发现原始包使用了三层限制机制：

1. **离线授权文件**：程序要求目录中存在 `license.key`。
2. **签名校验**：`fx_license_runtime.py` 使用内置 RSA 公钥参数校验 `license.key` 中 `license` 字段的规范 JSON 哈希。
3. **启动令牌**：`launcher.py run` 会在临时目录写入 `fx_guard_<product_id>.json`，并通过环境变量 `FX_RUN_TOKEN`、`FX_GUARD_PATH`、`FX_PRODUCT_ID` 传给入口文件；入口文件启动前会检查这些值。

原始包还将多数源码压缩为 `base85 + zlib` 字节串，然后用 `exec(compile(...))` 执行。这不是业务后门，但不适合开源审计和 GitHub 发布。

本发布版已经处理：

- 删除 `license.key`；
- 删除 `fx_license_runtime.py`；
- 删除旧授权说明；
- 删除所有 `__pycache__`；
- 还原压缩混淆源码为普通 `.py`；
- 重写 `launcher.py`，仅保留无授权启动功能；
- 修改 `main.py`，不再启动时自动 `pip install`；
- 删除旧版单文件 `whitehole2.py`，避免 v2/v3 双入口混淆。

### 后门检查结论

静态检查未发现硬编码远程控制地址、隐藏管理员口令、私钥、云端令牌、反向连接或主动外传逻辑。

需要注意的正常行为：

- 桌面模式会启动本地 Streamlit 子进程；
- `main.py` 会访问 `localhost` 健康检查地址；
- 侧边栏填写 API Key 后，`api/llm_client.py` 会向用户配置的 OpenAI-compatible API 发起请求；
- SGE 导出功能会把当前快照写到用户选择的本地文件路径。

## English

The original package used three protection layers:

1. **Offline license file**: the app required `license.key` in the project directory.
2. **Signature verification**: `fx_license_runtime.py` verified the canonical JSON hash of the `license` payload using embedded RSA public-key parameters.
3. **Launch token**: `launcher.py run` wrote a temporary `fx_guard_<product_id>.json` file and passed `FX_RUN_TOKEN`, `FX_GUARD_PATH`, and `FX_PRODUCT_ID` to the entry script; the entry script checked these values before running.

Most source files were additionally packed as `base85 + zlib` byte strings and executed with `exec(compile(...))`. This is not a business backdoor by itself, but it is unsuitable for open-source auditing and GitHub distribution.

This release has removed the protected-build artifacts and restored readable source code. Static inspection did not find hard-coded remote-control endpoints, hidden admin passwords, private keys, cloud tokens, reverse connections, or active exfiltration logic.
