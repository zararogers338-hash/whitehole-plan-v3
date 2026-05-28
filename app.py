# -*- coding: utf-8 -*-
"""
白洞计划 v3.0 — Streamlit 主 App
运行方式：streamlit run app.py
"""

import streamlit as st

from core.config import APP_TITLE, MODES
from sidebar import render_sidebar

# ─── 页面配置 ──────────────────────────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, layout="wide", page_icon="🌌")
st.title(f"🌌 {APP_TITLE}")

# 允许文本选中复制
st.markdown("""
<style>
* { user-select: text !important; -webkit-user-select: text !important; }
.stApp { background-color: #0E1117; }
.metric-container { padding: 8px; border-radius: 8px; background: rgba(255,255,255,0.05); }
</style>
""", unsafe_allow_html=True)

# ─── session_state 初始化 ──────────────────────────────────────────────────────
for key, default in [
    ("fig_traces", {}),
    ("selected_indices", []),
    ("perturbation", 0.0),
    ("virtual_title", ""),
    ("virtual_keywords", ""),
    ("virtual_year", 2024.0),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── 侧边栏 ────────────────────────────────────────────────────────────────────
ctx = render_sidebar()
files1 = ctx["files1"]
files2 = ctx["files2"]
all_files = files1 + files2
mode = ctx["mode"]

# ─── 模式路由 ──────────────────────────────────────────────────────────────────
if MODES[0] in mode:
    from modes import mode1_trajectory
    mode1_trajectory.render(all_files, ctx)

elif MODES[1] in mode:
    from modes import mode2_trend
    mode2_trend.render(all_files, ctx)

elif MODES[2] in mode:
    from modes import mode3_intervention
    mode3_intervention.render(all_files, ctx)

elif MODES[3] in mode:
    from modes import mode4_compare
    mode4_compare.render(files1, files2, ctx)

elif MODES[4] in mode:
    from modes import mode5_global
    mode5_global.render(all_files, ctx)

elif MODES[5] in mode:
    from modes import mode6_bias
    mode6_bias.render(all_files, ctx)

elif MODES[6] in mode:
    from modes import mode7_risk
    mode7_risk.render(files1, files2, ctx)

elif MODES[7] in mode:
    from modes import mode8_ai_detect
    mode8_ai_detect.render(all_files, ctx)

elif MODES[8] in mode:
    from modes import mode9_duplicate
    mode9_duplicate.render(all_files, ctx)

elif MODES[9] in mode:
    from modes import mode10_privacy
    mode10_privacy.render(all_files, ctx)

# ─── 页脚 ──────────────────────────────────────────────────────────────────────
st.divider()
st.caption(f"白洞计划 v3.0 · 学术命运模拟器 · 重制版 · 2026")
