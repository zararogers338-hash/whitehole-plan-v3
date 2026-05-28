# -*- coding: utf-8 -*-
"""模式5：社区共治 + 全球实时共识地图"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.text_utils import build_library_df
from core.horn_builder import build_horn_figure, apply_horn_layout
from core.sge_exporter import render_sge_export_ui
from api.llm_client import stream_ai_assistant


COUNTRY_COLORS = {
    "中国": "#FF3333",
    "美国": "#3366FF",
    "欧洲": "#33CC66",
    "其他": "#AAAAAA",
    "未知": "#DDDDDD",
}


def render(files: list, ctx: dict):
    if not files:
        st.info("👈 请上传论文构建全球共识地图")
        return

    df = build_library_df(files)
    country_counts = df["country"].value_counts().to_dict()
    t_min, t_max = df["time"].min(), df["time"].max()
    if t_min == t_max:
        t_min, t_max = t_min - 5, t_max + 5

    EXTRA = 3.0

    # ─── 国家分布统计 ─────────────────────────────────────────────────────────
    st.markdown("### 🌍 全球学术地理分布")
    cols = st.columns(len(COUNTRY_COLORS))
    for i, (country, color) in enumerate(COUNTRY_COLORS.items()):
        cnt = country_counts.get(country, 0)
        cols[i].metric(country, cnt, f"{'●' * min(cnt, 5)}")

    # ─── 号角图 ───────────────────────────────────────────────────────────────
    cache_key = "mode5_fig"
    if cache_key not in st.session_state.fig_traces:
        fig = build_horn_figure(t_min, t_max, extra=EXTRA)
        span = t_max - t_min + EXTRA + 1e-6
        rng = np.random.default_rng(5)
        for country, color in COUNTRY_COLORS.items():
            sub = df[df["country"] == country]
            if sub.empty:
                continue
            norm = (sub["time"].values - t_min) / span
            r = 1.0 + 0.8 * np.exp(norm)
            theta = rng.uniform(0, 2 * np.pi, len(sub))
            fig.add_trace(go.Scatter3d(
                x=r * np.cos(theta), y=r * np.sin(theta), z=sub["time"].values,
                mode="markers+text",
                marker=dict(size=10, color=color, opacity=0.85),
                text=sub["short_name"].tolist(),
                textposition="top center",
                name=country,
            ))
        st.session_state.fig_traces[cache_key] = fig.data

    fig = go.Figure(data=list(st.session_state.fig_traces[cache_key]))

    st.markdown("**图例**：🔴 中国 ｜ 🔵 美国 ｜ 🟢 欧洲 ｜ ⚪ 其他/未知")
    st.info("未来版本：真实全球数据匿名上传 + 实时更新 + 手性差异分析 + 2D全球地图模式")

    if st.button("🧠 AI分析全球学术共识"):
        country_summary = "、".join(f"{k} {v}篇" for k, v in country_counts.items())
        prompt = (
            f"分析当前论文库的全球学术分布：{country_summary}。"
            "预测未来5年全球学术重心转移方向、潜在突破地区、以及跨国合作的最佳机会领域。"
        )
        stream_ai_assistant(prompt, **_llm_kwargs(ctx))

    apply_horn_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

    import json
    render_sge_export_ui(
        mode_id="mode5",
        mode_name="全球实时共识地图",
        intel_lines={
            "国家分布": " | ".join(f"{k}:{v}" for k, v in country_counts.items()),
            "时间范围": f"{t_min:.1f} ~ {t_max:.1f}",
        },
        snapshots={
            "HORN_STRUCT.html": fig.to_html(full_html=True, include_plotlyjs="cdn"),
            "country_stats.json": json.dumps(country_counts, ensure_ascii=False),
        },
        inventory_files=files,
    )


def _llm_kwargs(ctx):
    return {k: ctx[k] for k in ("llm_mode", "selected_model_path", "base_url", "api_key", "model")}
