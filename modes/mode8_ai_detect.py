# -*- coding: utf-8 -*-
"""
模式8：审稿AI滥用检测器（全新实现）
从多个维度分析论文文本是否存在AI生成痕迹：
  - 词汇多样性（TTR）
  - 句子长度方差
  - 高频AI套话检测
  - 连接词密度
  - Burstiness（词频爆发度）
  - AI 特征词典匹配
注意：此工具仅供参考，不能替代专业学术不端检测系统。
"""

import re
import math
from collections import Counter

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core.text_utils import extract_text_from_file
from core.sge_exporter import render_sge_export_ui
from api.llm_client import stream_ai_assistant


# ─── AI 特征词典（中英文） ─────────────────────────────────────────────────────
AI_CLICHÉS_ZH = [
    "首先", "其次", "再次", "最后", "综上所述", "值得注意的是",
    "不可忽视", "至关重要", "举足轻重", "毋庸置疑", "显而易见",
    "在此背景下", "与此同时", "总体而言", "从长远来看",
    "不容小觑", "令人瞩目", "引人深思",
]
AI_CLICHÉS_EN = [
    "it is worth noting", "it is important to note", "furthermore",
    "moreover", "in conclusion", "in summary", "notably",
    "it should be noted", "importantly", "significantly",
    "this study aims", "the results suggest", "as shown in",
]

CONNECTOR_WORDS = {
    "however", "therefore", "moreover", "furthermore", "consequently",
    "nevertheless", "additionally", "subsequently",
    "然而", "因此", "此外", "此外", "consequently",
}


def _compute_ttr(text: str) -> float:
    """词汇类型-标记比 (TTR)：越高越多样。低 TTR 可能提示模板化写作。"""
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def _sentence_variance(text: str) -> float:
    """句子长度方差：AI 文本句子往往比较均匀，方差低。"""
    sentences = re.split(r'[。！？.!?]', text)
    lengths = [len(s.strip()) for s in sentences if len(s.strip()) > 5]
    if len(lengths) < 2:
        return 0.0
    return float(np.var(lengths))


def _cliche_density(text: str) -> tuple[float, list[str]]:
    """检测 AI 套话密度：命中数 / 总句数。"""
    text_lower = text.lower()
    hits = []
    for phrase in AI_CLICHÉS_ZH + AI_CLICHÉS_EN:
        if phrase.lower() in text_lower:
            hits.append(phrase)
    sentences = len(re.split(r'[。！？.!?]', text))
    density = len(hits) / max(sentences, 1)
    return round(density, 4), hits


def _connector_density(text: str) -> float:
    """连接词密度：AI 写作常滥用过渡连接词。"""
    words = re.findall(r'\b\w+\b', text.lower())
    connector_count = sum(1 for w in words if w in CONNECTOR_WORDS)
    return round(connector_count / max(len(words), 1), 4)


def _burstiness(text: str) -> float:
    """
    词频爆发度：真实人类写作有「话题跳跃」特征，词频分布更不均匀。
    AI 文本词频分布趋于平滑（低爆发度）。
    """
    words = re.findall(r'\b\w+\b', text.lower())
    if len(words) < 50:
        return 0.0
    counts = list(Counter(words).values())
    mu = np.mean(counts)
    sigma = np.std(counts)
    # Burstiness = (sigma - mu) / (sigma + mu)
    return round(float((sigma - mu) / (sigma + mu + 1e-9)), 4)


def _ai_score(ttr: float, sent_var: float, cliche_d: float, conn_d: float, burst: float) -> float:
    """
    综合 AI 痕迹评分（0-100，越高越像 AI 生成）。
    权重：套话密度 40% + 连接词密度 25% + 低 TTR 20% + 低句长方差 10% + 低爆发度 5%
    """
    score = 0.0
    score += min(cliche_d * 800, 40)          # 套话
    score += min(conn_d * 2500, 25)            # 连接词
    score += max(0, (0.7 - ttr) * 100) * 0.20  # 低多样性
    score += max(0, (500 - sent_var) / 500) * 10  # 低句长方差
    score += max(0, (0 - burst) * 5)           # 低爆发度
    return round(min(score, 100), 1)


def render(files: list, ctx: dict):
    if not files:
        st.info("👈 请上传论文文件进行 AI 滥用检测")
        return

    st.markdown("### 🤖 审稿 AI 滥用检测器")
    st.warning(
        "⚠️ 本工具基于统计特征检测，结果仅供参考，不具法律效力。"
        "AI 生成内容并不等于学术不端，请结合人工判断。"
    )

    results = []
    for file in files:
        text = extract_text_from_file(file)
        if len(text) < 100:
            continue
        ttr = _compute_ttr(text)
        sent_var = _sentence_variance(text)
        cliche_d, cliche_hits = _cliche_density(text)
        conn_d = _connector_density(text)
        burst = _burstiness(text)
        score = _ai_score(ttr, sent_var, cliche_d, conn_d, burst)
        results.append({
            "文件": file.name[:30],
            "AI痕迹分": score,
            "TTR": round(ttr, 3),
            "句长方差": round(sent_var, 1),
            "套话密度": cliche_d,
            "连接词密度": conn_d,
            "词频爆发度": burst,
            "命中套话": ", ".join(cliche_hits[:5]) or "无",
        })

    if not results:
        st.error("所有文件内容过短，无法检测")
        return

    import pandas as pd
    df = pd.DataFrame(results)

    # ─── 总览表格 ─────────────────────────────────────────────────────────────
    st.markdown("#### 📋 检测结果总览")
    def _color_score(val):
        if val > 70: return "background-color: #FF4444; color: white"
        if val > 40: return "background-color: #FFA500"
        return "background-color: #44CC44"
    st.dataframe(
        df[["文件", "AI痕迹分", "TTR", "套话密度", "连接词密度", "命中套话"]],
        use_container_width=True,
    )

    # ─── 可视化 ────────────────────────────────────────────────────────────────
    fig = go.Figure(go.Bar(
        x=df["文件"],
        y=df["AI痕迹分"],
        marker_color=[
            "#FF4444" if s > 70 else "#FFA500" if s > 40 else "#44CC44"
            for s in df["AI痕迹分"]
        ],
        text=[f"{s:.1f}" for s in df["AI痕迹分"]],
        textposition="outside",
    ))
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="高风险线(70)")
    fig.add_hline(y=40, line_dash="dash", line_color="orange", annotation_text="中风险线(40)")
    fig.update_layout(
        title="各论文 AI 痕迹评分（0=人类写作，100=高度AI生成）",
        yaxis=dict(range=[0, 110]),
        xaxis_title="论文",
        yaxis_title="AI痕迹分",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ─── 详细指标雷达（选中某篇） ──────────────────────────────────────────────
    selected_file = st.selectbox("查看详细维度分析", df["文件"].tolist(), key="ai_sel")
    row = df[df["文件"] == selected_file].iloc[0]
    dims = ["TTR多样性", "句长方差", "套话密度", "连接词密度", "词频爆发度"]
    # 标准化到 0-100（各维度方向对齐，越高越像AI）
    vals = [
        max(0, (0.7 - row["TTR"]) * 200),
        max(0, (500 - row["句长方差"]) / 5),
        min(row["套话密度"] * 800, 100),
        min(row["连接词密度"] * 2500, 100),
        max(0, -row["词频爆发度"] * 50),
    ]
    fig_r = go.Figure(go.Scatterpolar(
        r=vals + [vals[0]], theta=dims + [dims[0]],
        fill="toself", fillcolor="rgba(255,0,0,0.2)",
        line=dict(color="red"), name=selected_file,
    ))
    fig_r.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), title=f"AI特征雷达图：{selected_file}", height=400)
    st.plotly_chart(fig_r, use_container_width=True)
    st.caption(f"**命中套话**：{row['命中套话']}")

    # ─── AI 深度评审 ──────────────────────────────────────────────────────────
    if st.button("🧠 AI审稿员评审高风险论文", key="ai_review"):
        high_risk = df[df["AI痕迹分"] > 40]["文件"].tolist()
        if not high_risk:
            st.info("当前论文库未发现高风险文件")
        else:
            prompt = (
                f"以下论文的AI痕迹分析结果：\n"
                + "\n".join(
                    f"- {r['文件']}：{r['AI痕迹分']}分，套话：{r['命中套话']}"
                    for _, r in df.iterrows() if r["AI痕迹分"] > 40
                )
                + "\n\n请以严谨审稿人的视角，对这些论文进行AI滥用风险评估，"
                "并给出：可能的AI使用场景（完全生成/辅助润色/摘要生成）、"
                "建议的人工复核重点、以及如何在审稿阶段识别类似模式。"
            )
            stream_ai_assistant(prompt, **_llm_kwargs(ctx))

    import json
    render_sge_export_ui(
        mode_id="mode8",
        mode_name="审稿AI滥用检测报告",
        intel_lines={
            "检测论文数": len(results),
            "高风险(>70)": int((df["AI痕迹分"] > 70).sum()),
            "中风险(40-70)": int(((df["AI痕迹分"] > 40) & (df["AI痕迹分"] <= 70)).sum()),
        },
        snapshots={
            "ai_detection_report.json": json.dumps(results, ensure_ascii=False),
            "score_chart.html": fig.to_html(full_html=True, include_plotlyjs="cdn"),
        },
        inventory_files=files,
    )


def _llm_kwargs(ctx):
    return {k: ctx[k] for k in ("llm_mode", "selected_model_path", "base_url", "api_key", "model")}
