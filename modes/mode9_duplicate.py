# -*- coding: utf-8 -*-
"""
模式9：重复研究预警系统（全新实现）
基于 TF-IDF 向量余弦相似度检测论文库中的高度相似/重复研究。
"""

import re
import math
from collections import Counter, defaultdict

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core.text_utils import extract_text_from_file, extract_keywords
from core.config import STOPWORDS
from core.sge_exporter import render_sge_export_ui
from api.llm_client import stream_ai_assistant


# ─── 简化 TF-IDF 实现（不依赖 sklearn） ──────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """简单分词（中文字符 + 英文单词）。"""
    zh = re.findall(r'[\u4e00-\u9fff]{2,}', text)
    en = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    tokens = zh + en
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def _compute_tfidf(docs: list[list[str]]) -> list[dict[str, float]]:
    """计算 TF-IDF 向量列表。"""
    n = len(docs)
    # IDF
    df_counts: Counter = Counter()
    for doc in docs:
        df_counts.update(set(doc))
    idf = {term: math.log((n + 1) / (cnt + 1)) + 1 for term, cnt in df_counts.items()}
    # TF-IDF
    vecs = []
    for doc in docs:
        tf = Counter(doc)
        total = max(len(doc), 1)
        vec = {t: (c / total) * idf.get(t, 1.0) for t, c in tf.items()}
        vecs.append(vec)
    return vecs


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) & set(b)
    if not keys:
        return 0.0
    dot = sum(a[k] * b[k] for k in keys)
    norm_a = math.sqrt(sum(v**2 for v in a.values()))
    norm_b = math.sqrt(sum(v**2 for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def render(files: list, ctx: dict):
    if not files:
        st.info("👈 请上传论文库以进行重复研究预警")
        return
    if len(files) < 2:
        st.warning("至少需要2篇论文才能进行相似度分析")
        return

    st.markdown("### 🔁 重复研究预警系统")
    st.markdown("基于 TF-IDF 余弦相似度检测论文库中的高度相似研究，预防重复劳动。")

    threshold = st.slider("相似度阈值（超过此值视为潜在重复）", 0.1, 0.95, 0.5, 0.05, key="dup_thresh")

    with st.spinner("计算相似度矩阵…"):
        names = [f.name for f in files]
        docs = [_tokenize(extract_text_from_file(f)) for f in files]
        vecs = _compute_tfidf(docs)

        n = len(files)
        sim_matrix = np.zeros((n, n))
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                sim = _cosine(vecs[i], vecs[j])
                sim_matrix[i][j] = sim
                sim_matrix[j][i] = sim
                if sim >= threshold:
                    pairs.append((i, j, sim))

    # ─── 相似度热力图 ─────────────────────────────────────────────────────────
    short_names = [n[:15] + "…" if len(n) > 15 else n for n in names]
    fig_heat = go.Figure(go.Heatmap(
        z=sim_matrix,
        x=short_names,
        y=short_names,
        colorscale="RdYlGn_r",
        zmin=0, zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in sim_matrix],
        texttemplate="%{text}",
    ))
    fig_heat.update_layout(title="论文相似度矩阵（越红越相似）", height=max(400, n * 40 + 100))
    st.plotly_chart(fig_heat, use_container_width=True)

    # ─── 高相似对预警 ─────────────────────────────────────────────────────────
    st.markdown(f"#### ⚠️ 高相似度论文对（≥ {threshold:.2f}）")
    if not pairs:
        st.success(f"✅ 未发现相似度 ≥ {threshold:.2f} 的论文对，论文库研究视角较为多样。")
    else:
        pairs.sort(key=lambda x: -x[2])
        for i, j, sim in pairs:
            level = "🔴 极高" if sim > 0.8 else "🟠 高" if sim > 0.6 else "🟡 中"
            with st.expander(f"{level} | {sim:.3f} | {short_names[i]} ↔ {short_names[j]}"):
                kw_i = extract_keywords(extract_text_from_file(files[i]), top_n=8)
                kw_j = extract_keywords(extract_text_from_file(files[j]), top_n=8)
                col1, col2 = st.columns(2)
                col1.markdown(f"**{names[i]}**\n关键词：{', '.join(k for k,_ in kw_i)}")
                col2.markdown(f"**{names[j]}**\n关键词：{', '.join(k for k,_ in kw_j)}")

    # ─── 独特性评分 ────────────────────────────────────────────────────────────
    st.markdown("#### 📊 论文独特性评分（越高越独特）")
    uniqueness = []
    for i in range(n):
        others = [sim_matrix[i][j] for j in range(n) if j != i]
        avg_sim = np.mean(others) if others else 0
        uniqueness.append(round(1 - avg_sim, 3))

    fig_uniq = go.Figure(go.Bar(
        x=short_names,
        y=uniqueness,
        marker_color=["#44CC44" if u > 0.7 else "#FFA500" if u > 0.4 else "#FF4444" for u in uniqueness],
        text=[f"{u:.2f}" for u in uniqueness],
        textposition="outside",
    ))
    fig_uniq.update_layout(title="各论文独特性评分", yaxis=dict(range=[0, 1.1]))
    st.plotly_chart(fig_uniq, use_container_width=True)

    # ─── AI 重复性评估 ────────────────────────────────────────────────────────
    if st.button("🧠 AI分析重复研究风险", key="dup_ai"):
        high_sim_pairs = [(names[i], names[j], sim) for i, j, sim in pairs if sim > 0.6]
        prompt = (
            f"分析以下论文库的重复研究风险（共 {n} 篇，相似度阈值 {threshold}）：\n"
            + (
                "\n".join(f"- 《{a}》与《{b}》相似度 {s:.3f}" for a, b, s in high_sim_pairs[:5])
                if high_sim_pairs else "未发现高相似度论文对"
            )
            + "\n\n请分析：\n"
            "1. 这些相似研究属于正常学科积累还是潜在重复劳动？\n"
            "2. 应如何区分「延续性研究」和「重复性研究」？\n"
            "3. 给出避免重复研究的具体建议和差异化切入点。"
        )
        stream_ai_assistant(prompt, **_llm_kwargs(ctx))

    import json
    render_sge_export_ui(
        mode_id="mode9",
        mode_name="重复研究预警分析",
        intel_lines={
            "论文总数": n,
            "相似度阈值": threshold,
            "高相似对数": len(pairs),
        },
        snapshots={
            "similarity_matrix.json": json.dumps(sim_matrix.tolist()),
            "high_sim_pairs.json": json.dumps(
                [{"a": names[i], "b": names[j], "sim": round(sim, 4)} for i, j, sim in pairs],
                ensure_ascii=False,
            ),
            "heatmap.html": fig_heat.to_html(full_html=True, include_plotlyjs="cdn"),
        },
        inventory_files=files,
    )


def _llm_kwargs(ctx):
    return {k: ctx[k] for k in ("llm_mode", "selected_model_path", "base_url", "api_key", "model")}
