# -*- coding: utf-8 -*-
"""模式3：反向干预模拟器"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core.text_utils import build_library_df
from core.horn_builder import build_horn_figure, scatter_on_horn, apply_horn_layout
from core.sge_exporter import render_sge_export_ui
from api.llm_client import stream_ai_assistant


def render(files: list, ctx: dict):
    if not files:
        st.info("👈 请先加载论文库")
        return

    df = build_library_df(files)
    t_min, t_max = df["time"].min(), df["time"].max()
    if t_min == t_max:
        t_min, t_max = t_min - 5, t_max + 5

    # ─── 基础号角图缓存 ────────────────────────────────────────────────────────
    cache_key = "mode3_fig"
    if cache_key not in st.session_state.fig_traces:
        fig = build_horn_figure(t_min, t_max)
        fig = scatter_on_horn(
            fig, df["time"].values, df["short_name"].tolist(),
            t_min, t_max, color="#00AAFF", size=8, name="论文库", seed=0,
        )
        st.session_state.fig_traces[cache_key] = fig.data

    fig = go.Figure(data=list(st.session_state.fig_traces[cache_key]))

    st.markdown("### 💉 虚拟论文注入 → 观测场域扰动")

    # ─── 输入面板 ─────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        virtual_title = st.text_input(
            "虚拟论文标题",
            value=st.session_state.get("virtual_title", ""),
            key="vt",
        )
        virtual_keywords = st.text_input(
            "关键词（逗号分隔）",
            value=st.session_state.get("virtual_keywords", ""),
            key="vk",
        )
    with col2:
        virtual_year = st.slider(
            "注入年份",
            float(t_min), float(t_max),
            float(st.session_state.get("virtual_year", (t_min + t_max) / 2)),
            key="vy",
        )

    st.session_state["virtual_title"] = virtual_title
    st.session_state["virtual_keywords"] = virtual_keywords
    st.session_state["virtual_year"] = virtual_year

    if st.button("💥 注入扰动", key="inject_btn"):
        if virtual_title and virtual_keywords:
            import hashlib, random
            span = t_max - t_min + 1e-6
            norm = (virtual_year - t_min) / span
            r = 1.0 + 0.8 * np.exp(norm)
            theta = int(hashlib.sha256(virtual_title.encode()).hexdigest()[:8], 16) % 360 / 180 * np.pi

            fig.add_trace(go.Scatter3d(
                x=[r * np.cos(theta)], y=[r * np.sin(theta)], z=[virtual_year],
                mode="markers+text",
                marker=dict(size=25, color="purple", symbol="diamond-open"),
                text=[virtual_title[:18] + "…"],
                textposition="top center",
                name="虚拟注入论文",
            ))

            # 扰动强度由论文标题哈希 + 关键词数决定（可复现）
            h = int(hashlib.sha256((virtual_title + virtual_keywords).encode()).hexdigest()[:4], 16)
            perturbation = round(0.3 + (h % 100) / 150, 3)
            st.session_state["perturbation"] = perturbation
            st.session_state.fig_traces[cache_key] = fig.data

            st.markdown(f"**扰动强度：{perturbation:.3f}**（0.0 = 无影响，1.0 = 场域剧变）")
            if perturbation > 0.7:
                st.error("🟣 高扰动：可能引发手性翻转，场域剧变！")
            elif perturbation > 0.4:
                st.warning("🟢 中扰动：局部结构调整，有望进入核心区")
            else:
                st.info("🔵 低扰动：被现有场域吸收，无明显变化")
        else:
            st.error("请填写标题和关键词")

    if st.button("🧠 AI分析扰动影响", key="perturb_analyze"):
        p = st.session_state.get("perturbation", 0.0)
        if p == 0.0:
            st.warning("请先注入扰动再分析")
        else:
            prompt = (
                f"分析虚拟论文注入扰动结果：强度 {p:.3f}，"
                f"标题《{virtual_title}》，关键词：{virtual_keywords}，"
                f"注入时间点：{virtual_year:.1f} 年。"
                "预测对学术场域的短期（1-2年）和长期（5-10年）影响，以及潜在的新研究方向。"
            )
            stream_ai_assistant(prompt, **_llm_kwargs(ctx))

    apply_horn_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

    # ─── SGE 导出 ──────────────────────────────────────────────────────────────
    render_sge_export_ui(
        mode_id="mode3",
        mode_name="反向干预模拟（虚拟论文注入）",
        intel_lines={
            "虚拟论文": f"《{virtual_title}》",
            "关键词": virtual_keywords,
            "注入年份": f"{virtual_year:.2f}",
            "扰动强度": f"{st.session_state.get('perturbation', 0.0):.3f}",
        },
        snapshots={
            "HORN_STRUCT.html": fig.to_html(full_html=True, include_plotlyjs="cdn"),
        },
        inventory_files=files,
    )


def _llm_kwargs(ctx):
    return {k: ctx[k] for k in ("llm_mode", "selected_model_path", "base_url", "api_key", "model")}
