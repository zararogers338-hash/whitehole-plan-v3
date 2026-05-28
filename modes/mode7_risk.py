# -*- coding: utf-8 -*-
"""
模式7：跨学科移植风险模拟器（全新实现）
量化评估将领域A的研究方法/理论移植到领域B的风险与机遇：
  - 语义距离计算（关键词 Jaccard 相似度）
  - 时间错位分析
  - 移植难度评分（可解释性强的多维评分）
  - AI风险报告生成
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core.text_utils import extract_keywords, extract_text_from_file, extract_time_decimal
from core.sge_exporter import render_sge_export_ui
from api.llm_client import stream_ai_assistant


def _jaccard(set1: set, set2: set) -> float:
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)


def _compute_risk_profile(
    kw1: list[tuple[str, float]],
    kw2: list[tuple[str, float]],
    time1: float,
    time2: float,
) -> dict:
    """计算移植风险画像（0-100 分制，越高越难）。"""
    set1 = {k for k, _ in kw1}
    set2 = {k for k, _ in kw2}

    # 语义距离（1 - Jaccard）
    semantic_dist = 1.0 - _jaccard(set1, set2)

    # 时间错位
    time_gap = abs(time1 - time2)
    time_risk = min(time_gap / 20.0, 1.0)  # 20年以上视为最大风险

    # 词汇独特性（专业门槛）
    unique1 = len(set1 - set2)
    vocab_barrier = min(unique1 / max(len(set1), 1), 1.0)

    # 综合得分（加权）
    total_risk = (semantic_dist * 0.5 + time_risk * 0.2 + vocab_barrier * 0.3) * 100

    # 机遇评分（语义距离越大，新颖性越高）
    opportunity = semantic_dist * 80 + (1 - vocab_barrier) * 20

    # 共同词（迁移桥梁）
    bridge_kws = list(set1 & set2)[:10]

    return {
        "semantic_dist": round(semantic_dist, 3),
        "time_gap": round(time_gap, 1),
        "vocab_barrier": round(vocab_barrier, 3),
        "total_risk": round(total_risk, 1),
        "opportunity": round(opportunity, 1),
        "bridge_kws": bridge_kws,
        "unique_from_source": list(set1 - set2)[:10],
    }


def render(files1: list, files2: list, ctx: dict):
    if not files1 or not files2:
        st.info("👈 需要同时上传数据集1和数据集2才能进行跨学科移植风险分析")
        return

    st.markdown("### ⚗️ 跨学科移植风险模拟器")

    # ─── 提取两个领域的信息 ───────────────────────────────────────────────────
    with st.spinner("分析两个领域的知识结构…"):
        text1 = " ".join(extract_text_from_file(f) for f in files1)
        text2 = " ".join(extract_text_from_file(f) for f in files2)
        kw1 = extract_keywords(text1, top_n=30)
        kw2 = extract_keywords(text2, top_n=30)

        times1 = [extract_time_decimal(f.name) for f in files1]
        times2 = [extract_time_decimal(f.name) for f in files2]
        avg_time1 = np.mean(times1) if times1 else 2020.0
        avg_time2 = np.mean(times2) if times2 else 2020.0

    profile = _compute_risk_profile(kw1, kw2, avg_time1, avg_time2)

    # ─── 风险仪表盘 ───────────────────────────────────────────────────────────
    st.markdown("#### 🎯 移植风险仪表盘")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("综合风险分", f"{profile['total_risk']:.1f}/100",
                delta="高风险" if profile["total_risk"] > 70 else "中等" if profile["total_risk"] > 40 else "低风险")
    col2.metric("机遇评分", f"{profile['opportunity']:.1f}/100")
    col3.metric("时间错位", f"{profile['time_gap']:.1f} 年")
    col4.metric("语义距离", f"{profile['semantic_dist']:.3f}")

    # 风险雷达图
    categories = ["语义距离", "时间错位", "词汇门槛", "综合风险", "机遇评分"]
    values = [
        profile["semantic_dist"] * 100,
        min(profile["time_gap"] / 20 * 100, 100),
        profile["vocab_barrier"] * 100,
        profile["total_risk"],
        profile["opportunity"],
    ]
    fig_radar = go.Figure(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill="toself",
        fillcolor="rgba(255,100,0,0.3)",
        line=dict(color="#FF6600"),
        name="风险画像",
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(range=[0, 100])),
        title="移植风险多维雷达图",
        height=450,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # ─── 桥梁词与迁移词 ───────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 🌉 移植桥梁词（共同关键词）")
        if profile["bridge_kws"]:
            for kw in profile["bridge_kws"]:
                st.markdown(f"- **{kw}**")
        else:
            st.warning("两个领域几乎无共同词，移植难度极高")

    with col_b:
        st.markdown("#### 🚀 潜在迁移词（领域1特有）")
        for kw in profile["unique_from_source"][:10]:
            st.markdown(f"- {kw}")

    # ─── 风险等级说明 ─────────────────────────────────────────────────────────
    risk = profile["total_risk"]
    if risk > 70:
        st.error(f"🔴 高风险移植（{risk:.1f}分）：领域差异显著，需要大量基础工作，建议先建立跨领域合作团队再推进。")
    elif risk > 40:
        st.warning(f"🟡 中等风险移植（{risk:.1f}分）：存在一定障碍，建议选择桥梁词方向切入，分阶段推进。")
    else:
        st.success(f"🟢 低风险移植（{risk:.1f}分）：两个领域相对接近，移植可行性高，建议大胆推进。")

    # ─── AI深度分析 ───────────────────────────────────────────────────────────
    if st.button("🧠 AI生成完整移植战略报告", key="risk_ai"):
        kw1_str = ", ".join(k for k, _ in kw1[:10])
        kw2_str = ", ".join(k for k, _ in kw2[:10])
        prompt = (
            f"请为以下跨学科移植方案生成完整战略报告：\n\n"
            f"**源领域（数据集1）关键词**：{kw1_str}\n"
            f"**目标领域（数据集2）关键词**：{kw2_str}\n"
            f"**综合风险分**：{profile['total_risk']:.1f}/100\n"
            f"**桥梁词**：{', '.join(profile['bridge_kws']) or '无'}\n"
            f"**时间错位**：{profile['time_gap']:.1f} 年\n\n"
            "请输出：\n"
            "1. 移植可行性综合评估\n"
            "2. 最佳切入策略（选择哪些桥梁概念）\n"
            "3. 三大主要风险点及应对措施\n"
            "4. 预期产出的新研究方向（3个）\n"
            "5. 推荐团队组建建议"
        )
        stream_ai_assistant(prompt, **_llm_kwargs(ctx))

    import json
    render_sge_export_ui(
        mode_id="mode7",
        mode_name="跨学科移植风险分析",
        intel_lines={
            "综合风险分": f"{profile['total_risk']}/100",
            "机遇评分": f"{profile['opportunity']}/100",
            "语义距离": profile["semantic_dist"],
            "桥梁词": ", ".join(profile["bridge_kws"][:5]) or "无",
        },
        snapshots={
            "risk_profile.json": json.dumps(profile, ensure_ascii=False),
            "radar_chart.html": fig_radar.to_html(full_html=True, include_plotlyjs="cdn"),
        },
        inventory_files=files1 + files2,
    )


def _llm_kwargs(ctx):
    return {k: ctx[k] for k in ("llm_mode", "selected_model_path", "base_url", "api_key", "model")}
