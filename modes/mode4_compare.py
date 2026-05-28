# -*- coding: utf-8 -*-
"""模式4：多场域对比 + 跨学科移植"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.text_utils import build_library_df, extract_keywords, extract_text_from_file
from core.horn_builder import build_horn_figure, scatter_on_horn, apply_horn_layout
from core.sge_exporter import render_sge_export_ui
from api.llm_client import stream_ai_assistant


DATASET_COLORS = ["#00AAFF", "#FF00AA"]
TRANSPLANT_COLOR = "#FFAA00"


def render(files1: list, files2: list, ctx: dict):
    if not files1 and not files2:
        st.info("👈 请上传至少一个数据集")
        return

    datasets, kw_sets = [], []
    for idx, files in enumerate([files1, files2]):
        if files:
            df = build_library_df(files)
            df["dataset"] = f"数据集{idx+1}"
            datasets.append(df)
            all_text = " ".join(extract_text_from_file(f) for f in files)
            kw_sets.append(extract_keywords(all_text, top_n=20))
        else:
            kw_sets.append([])

    all_df = pd.concat(datasets, ignore_index=True)
    # ✅ 修复：正确处理 t_min/t_max 运算符优先级
    t_min, t_max = (all_df["time"].min(), all_df["time"].max()) if not all_df.empty else (2020, 2025)
    if t_min == t_max:
        t_min, t_max = t_min - 5, t_max + 5

    EXTRA = 3.0
    cache_key = "mode4_fig"
    if cache_key not in st.session_state.fig_traces:
        fig = build_horn_figure(t_min, t_max, extra=EXTRA)
        for i, df in enumerate(datasets):
            fig = scatter_on_horn(
                fig, df["time"].values, df["short_name"].tolist(),
                t_min, t_max, extra=EXTRA,
                color=DATASET_COLORS[i], size=10,
                name=df["dataset"].iloc[0],
                seed=i,
            )
        st.session_state.fig_traces[cache_key] = fig.data

    fig = go.Figure(data=list(st.session_state.fig_traces[cache_key]))

    # ─── 场域对比统计 ─────────────────────────────────────────────────────────
    st.markdown("### 📊 双场域叠加对比")
    if len(datasets) == 2:
        df1, df2 = datasets
        c1, c2, c3 = st.columns(3)
        c1.metric("数据集1 时间中心", f"{df1['time'].mean():.1f}")
        c2.metric("数据集2 时间中心", f"{df2['time'].mean():.1f}")
        c3.metric("时间差", f"{abs(df1['time'].mean()-df2['time'].mean()):.1f} 年")

        # 关键词重叠分析
        if kw_sets[0] and kw_sets[1]:
            set1 = {k for k, _ in kw_sets[0]}
            set2 = {k for k, _ in kw_sets[1]}
            overlap = set1 & set2
            unique1 = set1 - set2
            unique2 = set2 - set1
            st.markdown(
                f"**关键词重叠**：{len(overlap)} 个共同词 | "
                f"数据集1独有：{len(unique1)} | 数据集2独有：{len(unique2)}"
            )
            if overlap:
                st.info(f"共同关键词：{', '.join(list(overlap)[:10])}")

        # 跨学科移植
        st.markdown("### 🔄 一键跨学科移植")
        if st.button("从数据集1移植关键词到数据集2", key="transplant_btn"):
            transplanted = datasets[0].copy()
            rng = np.random.default_rng(99)
            transplanted["time"] += rng.uniform(2.0, 4.0, len(transplanted))
            span = t_max - t_min + EXTRA + 1e-6
            t_norm = (transplanted["time"] - t_min) / span
            t_r = 1.0 + 0.8 * np.exp(t_norm)
            t_theta = rng.uniform(0, 2 * np.pi, len(transplanted))
            fig.add_trace(go.Scatter3d(
                x=t_r * np.cos(t_theta), y=t_r * np.sin(t_theta), z=transplanted["time"],
                mode="markers",
                marker=dict(size=12, color=TRANSPLANT_COLOR, symbol="diamond-open"),
                name="移植关键词",
            ))
            st.session_state.fig_traces[cache_key] = fig.data
            st.success("✅ 移植完成：橙色开放菱形为移植后论文在新场域中的预测落点")

        if st.button("🧠 AI分析移植潜力", key="transplant_ai"):
            kw1 = [k for k, _ in kw_sets[0][:10]]
            kw2 = [k for k, _ in kw_sets[1][:10]]
            prompt = (
                f"分析从领域1向领域2的跨学科知识移植潜力。\n"
                f"领域1关键词：{', '.join(kw1)}\n"
                f"领域2关键词：{', '.join(kw2)}\n"
                "给出：移植可行性评估、预期突破方向、主要风险点、推荐切入角度。"
            )
            stream_ai_assistant(prompt, **_llm_kwargs(ctx))

    apply_horn_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

    render_sge_export_ui(
        mode_id="mode4",
        mode_name="多场域对比与跨学科移植",
        intel_lines={"数据集数量": len(datasets), "数据集1": len(files1), "数据集2": len(files2)},
        snapshots={"HORN_STRUCT.html": fig.to_html(full_html=True, include_plotlyjs="cdn")},
        inventory_files=files1 + files2,
    )


def _llm_kwargs(ctx):
    return {k: ctx[k] for k in ("llm_mode", "selected_model_path", "base_url", "api_key", "model")}
