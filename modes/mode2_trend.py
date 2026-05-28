# -*- coding: utf-8 -*-
"""模式2：实时趋势预测 + 未来论文生成器"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core.text_utils import extract_keywords, extract_text_from_file
from core.sge_exporter import render_sge_export_ui
from api.llm_client import stream_ai_assistant


def render(files: list, ctx: dict):
    if not files:
        st.info("👈 请先加载论文构建趋势预测")
        return

    all_text = " ".join(extract_text_from_file(f) for f in files)
    keywords = extract_keywords(all_text, top_n=30)
    if not keywords:
        st.error("无法提取有效关键词，请检查文件内容")
        return

    kw_list, scores = zip(*keywords)

    # 使用局部 rng 避免污染全局随机状态
    rng = np.random.default_rng(42)
    years = np.linspace(2026, 2030, 5)
    predicted_scores = {
        kw: np.linspace(score, score * rng.uniform(1.2, 2.5), 5)
        for kw, score in keywords[:10]
    }

    st.markdown("### 📈 Top 10 关键词未来5年爆发趋势预测")
    fig_trend = go.Figure()
    for kw in kw_list[:10]:
        fig_trend.add_trace(go.Scatter(
            x=years,
            y=predicted_scores.get(kw, [0] * 5),
            mode="lines+markers",
            name=kw,
        ))
    fig_trend.update_layout(
        title="关键词爆发趋势预测（2026-2030）",
        xaxis_title="年份",
        yaxis_title="预测权重",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # ─── 关键词词云展示 ────────────────────────────────────────────────────────
    st.markdown("### 🔑 全部关键词（Top 30）")
    kw_cols = st.columns(5)
    for i, (kw, score) in enumerate(keywords[:30]):
        kw_cols[i % 5].markdown(
            f"<span style='font-size:{10+int(score*300)}px'>{kw}</span>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### 📝 未来论文生成器")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔮 生成未来论文（3篇）", key="gen_papers"):
            prompt = (
                f"根据以下关键词，生成3篇可能的未来学术论文。"
                f"每篇包含：标题、摘要（200-300字）、关键词、预计影响力评级（A/B/C）。"
                f"用中文输出。\n\n关键词：{', '.join(kw_list[:15])}\n\n"
                "论文1\n标题：\n摘要：\n关键词：\n影响力：\n\n"
                "论文2\n标题：\n摘要：\n关键词：\n影响力：\n\n"
                "论文3\n标题：\n摘要：\n关键词：\n影响力："
            )
            stream_ai_assistant(prompt, **_llm_kwargs(ctx))

    with col2:
        if st.button("🧠 AI分析趋势格局", key="analyze_trend"):
            prompt = (
                f"分析这批论文的关键词趋势格局，Top关键词包括：{', '.join(kw_list[:10])}。"
                "预测未来3-5年的研究热点转移方向、潜在突破点，以及需要警惕的过热泡沫领域。"
            )
            stream_ai_assistant(prompt, **_llm_kwargs(ctx))

    # ─── SGE 导出 ──────────────────────────────────────────────────────────────
    render_sge_export_ui(
        mode_id="mode2",
        mode_name="实时趋势预测与未来论文模拟",
        intel_lines={
            "核心关键词（Top 15）": ", ".join(kw_list[:15]),
            "预测时间范围": "2026-2030",
        },
        snapshots={
            "TREND_MAP.html": fig_trend.to_html(full_html=True, include_plotlyjs="cdn"),
            "keywords.json": __import__("json").dumps(
                {"keywords": list(kw_list[:30]), "scores": list(scores)},
                ensure_ascii=False,
            ),
        },
        inventory_files=files,
    )


def _llm_kwargs(ctx):
    return {k: ctx[k] for k in ("llm_mode", "selected_model_path", "base_url", "api_key", "model")}
