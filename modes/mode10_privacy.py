# -*- coding: utf-8 -*-
"""
模式10：隐私匿名共识地图（全新实现）
将论文库信息完全匿名化后，用网络图展示关键词共识结构：
  - 论文以哈希匿名化（不显示真实文件名）
  - 关键词共现网络图（节点大小 = 频率，边粗细 = 共现强度）
  - 「共识岛屿」检测（高度互连的关键词群）
  - 支持将匿名快照安全导出为 SGE
"""

import re
import hashlib
from collections import Counter, defaultdict

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core.text_utils import extract_text_from_file, extract_keywords
from core.sge_exporter import render_sge_export_ui
from api.llm_client import stream_ai_assistant


def _anonymize(name: str) -> str:
    """将文件名哈希为匿名标识符。"""
    h = hashlib.sha256(name.encode()).hexdigest()[:8].upper()
    return f"PAPER-{h}"


def _build_cooccurrence(files: list, top_n: int = 20) -> dict:
    """
    构建关键词共现矩阵。
    co[kw1][kw2] = 在多少篇文章中同时出现
    """
    kw_sets: list[set] = []
    global_counter: Counter = Counter()
    for f in files:
        text = extract_text_from_file(f)
        kws = {k for k, _ in extract_keywords(text, top_n=top_n)}
        kw_sets.append(kws)
        global_counter.update(kws)

    top_kws = [k for k, _ in global_counter.most_common(top_n)]

    co: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for kws in kw_sets:
        relevant = [k for k in top_kws if k in kws]
        for i in range(len(relevant)):
            for j in range(i + 1, len(relevant)):
                co[relevant[i]][relevant[j]] += 1
                co[relevant[j]][relevant[i]] += 1

    return {"top_kws": top_kws, "co": {k: dict(v) for k, v in co.items()}, "freq": dict(global_counter)}


def _layout_network(kws: list[str]) -> dict[str, tuple[float, float]]:
    """简单圆形布局（不依赖 networkx）。"""
    n = len(kws)
    positions = {}
    for i, kw in enumerate(kws):
        angle = 2 * np.pi * i / max(n, 1)
        positions[kw] = (np.cos(angle), np.sin(angle))
    return positions


def render(files: list, ctx: dict):
    if not files:
        st.info("👈 请上传论文构建匿名共识地图")
        return

    st.markdown("### 🕵️ 隐私匿名共识地图")
    st.info(
        "🔒 所有论文已完全匿名化（文件名转为哈希ID），"
        "只展示关键词层面的共识结构，不泄露任何个体信息。"
    )

    top_n = st.slider("关键词数量", 10, 30, 20, key="priv_top_n")
    min_cooc = st.slider("最小共现次数（过滤弱连接）", 1, max(len(files) // 2, 2), 1, key="priv_cooc")

    with st.spinner("构建匿名共识网络…"):
        result = _build_cooccurrence(files, top_n=top_n)
        top_kws = result["top_kws"]
        co = result["co"]
        freq = result["freq"]

    if not top_kws:
        st.error("无法提取足够关键词，请检查文件内容")
        return

    pos = _layout_network(top_kws)

    # ─── 构建网络图 ────────────────────────────────────────────────────────────
    edge_traces = []
    for kw1, neighbors in co.items():
        if kw1 not in pos:
            continue
        for kw2, cnt in neighbors.items():
            if kw2 not in pos or cnt < min_cooc or kw1 >= kw2:
                continue
            x0, y0 = pos[kw1]
            x1, y1 = pos[kw2]
            width = min(cnt * 2, 8)
            edge_traces.append(go.Scatter(
                x=[x0, x1, None], y=[y0, y1, None],
                mode="lines",
                line=dict(width=width, color=f"rgba(100,150,255,{min(cnt/len(files), 0.8):.2f})"),
                hoverinfo="none",
                showlegend=False,
            ))

    max_freq = max(freq.values()) if freq else 1
    node_x = [pos[k][0] for k in top_kws if k in pos]
    node_y = [pos[k][1] for k in top_kws if k in pos]
    node_sizes = [10 + freq.get(k, 0) / max_freq * 40 for k in top_kws if k in pos]
    node_colors = [freq.get(k, 0) for k in top_kws if k in pos]

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        hovermode="closest",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            colorscale="Viridis",
            colorbar=dict(title="文件覆盖数"),
            line=dict(width=2, color="white"),
        ),
        text=[k for k in top_kws if k in pos],
        textposition="top center",
        hovertext=[f"{k}: 出现 {freq.get(k,0)} 次" for k in top_kws if k in pos],
        name="关键词节点",
    )

    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(
        title="🔒 匿名关键词共识网络图（节点大小=频率，边粗=共现强度）",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=600,
        plot_bgcolor="#0E1117",
        paper_bgcolor="#0E1117",
        font=dict(color="white"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ─── 匿名论文清单 ─────────────────────────────────────────────────────────
    st.markdown("#### 🔐 匿名论文清单")
    anon_map = {f.name: _anonymize(f.name) for f in files}
    cols = st.columns(3)
    for i, (orig, anon_id) in enumerate(anon_map.items()):
        cols[i % 3].markdown(f"`{anon_id}`")

    st.caption(f"共 {len(files)} 篇论文，真实文件名已加密，以上ID无法反推原始文件名。")

    # ─── 共识岛屿检测 ─────────────────────────────────────────────────────────
    st.markdown("#### 🏝️ 共识岛屿检测（高度互连关键词群）")
    islands = _detect_islands(top_kws, co, min_cooc)
    if islands:
        for i, island in enumerate(islands[:5], 1):
            st.markdown(f"**岛屿 {i}**：{' · '.join(island)}")
    else:
        st.info("暂未发现高度互连的关键词群，尝试降低最小共现次数")

    # ─── AI共识分析 ───────────────────────────────────────────────────────────
    if st.button("🧠 AI分析匿名共识结构", key="priv_ai"):
        top_pairs = []
        for kw1, neighbors in co.items():
            for kw2, cnt in neighbors.items():
                if cnt >= min_cooc and kw1 < kw2:
                    top_pairs.append((kw1, kw2, cnt))
        top_pairs.sort(key=lambda x: -x[2])
        prompt = (
            f"分析以下学术论文库（{len(files)}篇，已匿名）的关键词共识结构：\n"
            f"核心关键词（Top 10）：{', '.join(top_kws[:10])}\n"
            f"最强共现对（Top 5）：{', '.join(f'{a}-{b}({c})' for a,b,c in top_pairs[:5])}\n"
            f"共识岛屿：{'; '.join(' '.join(isl) for isl in islands[:3]) or '无'}\n\n"
            "请分析：该论文库的核心知识共识是什么？"
            "存在哪些相互强化的研究范式？哪些边缘关键词可能是新兴方向？"
        )
        stream_ai_assistant(prompt, **_llm_kwargs(ctx))

    import json
    render_sge_export_ui(
        mode_id="mode10",
        mode_name="隐私匿名共识地图",
        intel_lines={
            "匿名论文数": len(files),
            "顶级关键词数": len(top_kws),
            "共识岛屿数": len(islands),
            "隐私保护": "已启用（文件名哈希化）",
        },
        snapshots={
            "network_chart.html": fig.to_html(full_html=True, include_plotlyjs="cdn"),
            "consensus_data.json": json.dumps(
                {"keywords": top_kws, "freq": {k: freq.get(k, 0) for k in top_kws}, "islands": islands},
                ensure_ascii=False,
            ),
            "anon_manifest.json": json.dumps(
                {v: "（原始文件名已隐去）" for v in anon_map.values()},
                ensure_ascii=False,
            ),
        },
        inventory_files=[],  # 不记录真实文件名
    )


def _detect_islands(kws: list[str], co: dict, min_cooc: int) -> list[list[str]]:
    """用简单 Union-Find 检测强连通子图（岛屿）。"""
    parent = {k: k for k in kws}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    for kw1, neighbors in co.items():
        for kw2, cnt in neighbors.items():
            if cnt >= min_cooc and kw1 in parent and kw2 in parent:
                union(kw1, kw2)

    groups: dict[str, list] = defaultdict(list)
    for kw in kws:
        groups[find(kw)].append(kw)

    return [g for g in sorted(groups.values(), key=len, reverse=True) if len(g) >= 3]


def _llm_kwargs(ctx):
    return {k: ctx[k] for k in ("llm_mode", "selected_model_path", "base_url", "api_key", "model")}
