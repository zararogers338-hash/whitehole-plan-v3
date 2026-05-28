# 🌌 白洞计划 Whitehole Plan v3.0 Open

> 中文：一个面向论文库、研究主题与学术场域的本地可视化分析工具。  
> English: A local visual analysis toolkit for paper collections, research topics, and academic-field simulation.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 中文说明

**白洞计划（Whitehole Plan）** 是一个基于 Streamlit + Plotly + pywebview 的学术分析与模拟工具。它可以读取 PDF、DOCX、TXT、MD 等文档，提取文本与关键词，并用三维“学术号角图”、趋势图、相似度矩阵、匿名共识网络等方式展示一个论文库的结构。

这个版本是 **开源发布版**：

- 已移除 `license.key` 授权文件要求；
- 已移除机器指纹绑定；
- 已移除启动令牌校验；
- 已将原本压缩混淆的 Python 代码还原为明文源码；
- 已删除 `__pycache__`、旧授权说明、测试授权文件和混淆发布残留。

### 主要功能

| 模式 | 功能 |
|---|---|
| 1 | 个人学术命运轨迹：将论文按时间/位置投射到三维学术号角图 |
| 2 | 实时趋势预测 + 未来论文生成器：基于关键词预测未来主题 |
| 3 | 反向干预模拟器：模拟新论文/新关键词对场域的扰动 |
| 4 | 多场域对比 + 跨学科移植：比较两个论文库的关键词结构 |
| 5 | 社区共治 + 全球实时共识地图：用国家/地区线索估计论文分布 |
| 6 | 引用偏差探测器：检查地理、时间、关键词自偏差 |
| 7 | 跨学科移植风险模拟器：估计概念移植的机会与风险 |
| 8 | 审稿 AI 滥用检测器：用启发式指标寻找疑似 AI 套话风险 |
| 9 | 重复研究预警系统：用 TF-IDF 余弦相似度发现潜在重复研究 |
| 10 | 隐私匿名共识地图：文件名哈希匿名，只展示关键词共识网络 |

### 安装

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 运行

桌面窗口模式：

```bash
python launcher.py run
# 或
python main.py
```

浏览器模式：

```bash
streamlit run app.py
```

Windows 用户也可以双击：

```text
run.bat
启动白洞计划.bat
```

### 本地模型与 API

- 如果要使用本地 GGUF 模型，把 `.gguf` 文件放入 `models/` 目录。
- 如果使用自定义 API，在侧边栏填写 API Base URL、API Key 和模型名。
- API Key 只在当前 Streamlit 会话中使用，不会写入仓库文件。

### SGE 文件

SGE 是本项目导出的“黑盒快照”格式，本质上是一个 ZIP 包，包含：

- `MANIFEST.TXT`：当前分析视图的说明；
- `SNAPSHOTS/`：图表 HTML、JSON 数据或文本快照。

### 仓库建议

推荐仓库名：`whitehole-plan`  
推荐发布版本：`v3.0.0-open.1`  
推荐 Topics：

```text
streamlit, academic-analysis, research-tools, paper-analysis, knowledge-map, llm, gguf, pywebview, plotly, tf-idf, whitehole-plan, 白洞计划, 学术分析, 论文分析, 知识图谱
```

---

## English

**Whitehole Plan** is a local Streamlit + Plotly + pywebview toolkit for academic-field visualization and simulation. It ingests PDF, DOCX, TXT, and Markdown files, extracts text and keywords, and visualizes a paper collection through 3D academic “horn” diagrams, trend charts, similarity matrices, and anonymized consensus networks.

This is the **open-source release**:

- `license.key` is no longer required;
- machine fingerprint binding has been removed;
- launch-token checks have been removed;
- previously compressed/obfuscated Python files have been restored to readable source code;
- `__pycache__`, old license notes, test license files, and protected-build leftovers have been removed.

### Features

| Mode | Feature |
|---|---|
| 1 | Personal academic trajectory: maps papers onto a 3D academic horn diagram |
| 2 | Trend prediction + future paper generator: predicts future topics from keywords |
| 3 | Reverse intervention simulator: simulates how new papers/keywords disturb a field |
| 4 | Multi-field comparison + interdisciplinary transfer: compares keyword structures |
| 5 | Community governance + global consensus map: estimates geographic distribution |
| 6 | Citation-bias detector: checks geographic, temporal, and keyword self-bias |
| 7 | Interdisciplinary transfer-risk simulator: estimates opportunity and risk |
| 8 | AI-reviewer-abuse detector: heuristic detection of formulaic AI-style writing |
| 9 | Duplicate-research warning system: TF-IDF cosine similarity across papers |
| 10 | Privacy-preserving anonymous consensus map: hashed filenames and keyword networks |

### Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Run

Desktop mode:

```bash
python launcher.py run
# or
python main.py
```

Browser mode:

```bash
streamlit run app.py
```

### Local models and API

- Put local `.gguf` models in `models/`.
- For an external API, enter the API Base URL, API Key, and model name in the sidebar.
- API keys are only used in the active Streamlit session and are not written into repository files.

### Suggested repository metadata

Suggested repository name: `whitehole-plan`  
Suggested release tag: `v3.0.0-open.1`  
Suggested topics:

```text
streamlit, academic-analysis, research-tools, paper-analysis, knowledge-map, llm, gguf, pywebview, plotly, tf-idf, whitehole-plan
```

---

## Safety / Security Notes

This repository does not contain a remote-control backend or hidden server. Network access is limited to:

1. local Streamlit health checks at `localhost`;  
2. optional user-configured LLM API calls;  
3. dependency installation done manually through `pip install -r requirements.txt`.

See [`RELEASE_AUDIT.md`](RELEASE_AUDIT.md) for the release-cleaning audit.
