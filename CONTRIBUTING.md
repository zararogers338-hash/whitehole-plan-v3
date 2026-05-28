# Contributing / 贡献指南

欢迎提交 Issue 和 Pull Request。

建议流程：

1. Fork 本仓库。
2. 创建功能分支：`git checkout -b feature/your-change`。
3. 安装依赖：`pip install -r requirements.txt`。
4. 运行：`streamlit run app.py` 或 `python launcher.py run`。
5. 提交 PR 前，请至少运行一次语法检查：`python -m py_compile $(find . -name "*.py" -not -path "*/.venv/*")`。

Please keep changes readable, documented, and free of hard-coded credentials.
