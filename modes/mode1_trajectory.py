# -*- coding: utf-8 -*-
"""模式1：个人学术命运轨迹"""

import streamlit as st

from core.text_utils import build_library_df
from core.horn_builder import (
    build_horn_figure, scatter_on_horn, highlight_on_horn, apply_horn_layout
)
from core.sge_exporter import render_sge_export_ui
from api.llm_client import stream_ai_assistant


def render(files: list, ctx: dict):
    if not files:
        st.info("👈 请在侧边栏上传文件构建学术场域")
        return

    df = build_library_df(files)
    t_min, t_max = df["time"].min(), df["time"].max()
    if t_min == t_max:
        t_min, t_max = t_min - 5, t_max + 5

    # ─── 号角图（带 session_state 缓存） ─────────────────────────────────────
    cache_key = "mode1_fig"
    if cache_key not in st.session_state.fig_traces:
        fig = build_horn_figure(t_min, t_max)
        fig = scatter_on_horn(
            fig,
            times=df["time"].values,
            labels=df["short_name"].tolist(),
            t_min=t_min, t_max=t_max,
            color="#00AAFF", size=8,
            name="论文库",
            seed=42,
        )
        st.session_state.fig_traces[cache_key] = fig.data

    fig = __import__("plotly.graph_objects", fromlist=["Figure"]).Figure(
        data=st.session_state.fig_traces[cache_key]
    )

    # ─── 论文选择 ─────────────────────────────────────────────────────────────
    st.subheader("🔴 选择你的论文（支持多选，高亮显示）")
    selected_indices = []
    cols = st.columns(3)
    prev = st.session_state.get("selected_indices", [])
    for idx, row in df.iterrows():
        with cols[idx % 3]:
            checked = st.checkbox(
                row["short_name"],
                key=f"chk1_{idx}",
                value=idx in prev,
            )
            if checked:
                selected_indices.append(idx)
    st.session_state["selected_indices"] = selected_indices

    # ─── 高亮 ──────────────────────────────────────────────────────────────────
    import plotly.graph_objects as go
    fig_display = go.Figure(data=list(fig.data[:2]))
    for sel_idx in selected_indices:
        row = df.iloc[sel_idx]
        fig_display = highlight_on_horn(
            fig_display, row["time"], row["name"],
            t_min, t_max, color="red", size=20,
        )
        median = (t_min + t_max) / 2
        pos = "前沿区域 🚀" if row["time"] > median else "经典区域 📚"
        st.markdown(
            f"**{row['name']}** ｜ 位置：{row['time']:.2f} ｜ {pos}"
            f"（场域范围 {t_min:.1f}–{t_max:.1f}）"
        )

    apply_horn_layout(fig_display)
    st.plotly_chart(fig_display, use_container_width=True)

    # ─── AI 分析 ───────────────────────────────────────────────────────────────
    if selected_indices and st.button("🧠 AI分析选中论文的学术命运"):
        sel_titles = [df.iloc[i]["name"] for i in selected_indices]
        prompt = (
            f"分析以下论文在学术场域中的位置与命运潜力。"
            f"时间范围 {t_min:.1f}–{t_max:.1f} 年。\n"
            f"论文列表：\n" + "\n".join(f"- {t}" for t in sel_titles)
        )
        st.markdown("### 🧠 AI命运分析")
        stream_ai_assistant(prompt, **_llm_kwargs(ctx))

    # ─── SGE 导出 ──────────────────────────────────────────────────────────────
    selected_str = "；".join(df.iloc[i]["name"] for i in selected_indices) or "无"
    render_sge_export_ui(
        mode_id="mode1",
        mode_name="个人学术命运轨迹观测",
        intel_lines={
            "选中论文": selected_str,
            "时间范围": f"{t_min:.2f} ~ {t_max:.2f}",
            "总论文数": len(df),
        },
        snapshots={
            "HORN_STRUCT.html": fig_display.to_html(full_html=True, include_plotlyjs="cdn"),
            "library_data.json": df[["name", "short_name", "time"]].to_json(orient="records"),
        },
        inventory_files=files,
    )


def _llm_kwargs(ctx: dict) -> dict:
    return {k: ctx[k] for k in ("llm_mode", "selected_model_path", "base_url", "api_key", "model")}
