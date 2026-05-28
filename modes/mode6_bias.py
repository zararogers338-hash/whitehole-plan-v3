# -*- coding: utf-8 -*-
"""
模式6：引用偏差探测器（全新实现）
分析论文库中的三类引用偏差：
  - 地理偏差（哪些国家被过度/欠引用）
  - 时间偏差（是否过度引用近年 or 经典论文）
  - 自引偏差（同一机构/关键词反复引用自身）
"""

import re
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.text_utils import build_library_df, extract_keywords, extract_text_from_file, get_country
from core.config import COUNTRY_KEYWORDS
from core.sge_exporter import render_sge_export_ui
from api.llm_client import stream_ai_assistant


def _extract_citations(text: str) -> list[str]:
    """从文本中提取疑似引用条目（方括号编号 or 括号年份）。"""
    refs = re.findall(r"\[(\d+)\]", text)           # [1] [2]
    year_refs = re.findall(r"\((\d{4})\)", text)     # (2020)
    return refs + year_refs


def _detect_geo_bias(df: pd.DataFrame) -> pd.DataFrame:
    """统计各国论文数量，计算相对于均匀分布的偏差系数。"""
    counts = df["country"].value_counts()
    total = len(df)
    expected = total / max(len(counts), 1)
    bias_df = pd.DataFrame({
        "国家/地区": counts.index,
        "论文数": counts.values,
        "期望均匀": round(expected, 1),
        "偏差系数": ((counts.values - expected) / (expected + 1e-6)).round(3),
    })
    return bias_df


def _detect_temporal_bias(df: pd.DataFrame) -> dict:
    """检测时间偏差：近5年 vs 5年前论文比例。"""
    import datetime
    current_year = datetime.datetime.now().year
    recent = (df["time"] >= current_year - 5).sum()
    older = len(df) - recent
    recency_ratio = recent / max(len(df), 1)
    return {
        "近5年论文数": int(recent),
        "5年前论文数": int(older),
        "近期化率": f"{recency_ratio:.1%}",
        "偏向": "⚠️ 过度引用近期文献" if recency_ratio > 0.75
                else "⚠️ 过度依赖经典文献" if recency_ratio < 0.25
                else "✅ 时间分布较均衡",
    }


def _detect_keyword_self_bias(files: list) -> list[tuple[str, int]]:
    """检测关键词自引偏差：同一关键词在所有文件中重复出现的频率。"""
    kw_counter: Counter = Counter()
    for f in files:
        text = extract_text_from_file(f)
        kws = extract_keywords(text, top_n=10)
        kw_counter.update(k for k, _ in kws)
    # 在超过50%文件中出现的关键词视为潜在自引
    threshold = max(len(files) * 0.5, 2)
    return [(kw, cnt) for kw, cnt in kw_counter.most_common(20) if cnt >= threshold]


def render(files: list, ctx: dict):
    if not files:
        st.info("👈 请上传论文库以进行引用偏差分析")
        return

    st.markdown("### 🔍 引用偏差探测器")
    st.markdown("系统自动检测你的论文库中的三类引用偏差，帮助识别盲区与倾向性。")

    df = build_library_df(files)

    tab1, tab2, tab3 = st.tabs(["🌍 地理偏差", "📅 时间偏差", "♻️ 关键词自引偏差"])

    # ─── Tab1：地理偏差 ───────────────────────────────────────────────────────
    with tab1:
        st.markdown("#### 各国/地区论文分布偏差")
        bias_df = _detect_geo_bias(df)
        st.dataframe(bias_df, use_container_width=True)

        fig_geo = go.Figure(go.Bar(
            x=bias_df["国家/地区"],
            y=bias_df["偏差系数"],
            marker_color=[
                "#FF4444" if v > 0.3 else "#4444FF" if v < -0.3 else "#AAAAAA"
                for v in bias_df["偏差系数"]
            ],
            text=bias_df["偏差系数"].apply(lambda x: f"{x:+.2f}"),
            textposition="outside",
        ))
        fig_geo.update_layout(
            title="地理偏差系数（正值=过度引用，负值=欠引用）",
            yaxis_title="偏差系数",
            xaxis_title="国家/地区",
        )
        st.plotly_chart(fig_geo, use_container_width=True)

        over = bias_df[bias_df["偏差系数"] > 0.3]["国家/地区"].tolist()
        under = bias_df[bias_df["偏差系数"] < -0.3]["国家/地区"].tolist()
        if over:
            st.warning(f"⚠️ 可能存在地理偏向：过度引用 → {', '.join(over)}")
        if under:
            st.info(f"💡 欠引用地区（建议补充）：{', '.join(under)}")

    # ─── Tab2：时间偏差 ───────────────────────────────────────────────────────
    with tab2:
        st.markdown("#### 论文时间分布分析")
        temp_bias = _detect_temporal_bias(df)
        c1, c2, c3 = st.columns(3)
        c1.metric("近5年论文", temp_bias["近5年论文数"])
        c2.metric("5年前论文", temp_bias["5年前论文数"])
        c3.metric("近期化率", temp_bias["近期化率"])
        st.markdown(f"**判断**：{temp_bias['偏向']}")

        # 时间分布直方图
        fig_time = go.Figure(go.Histogram(
            x=df["time"].apply(lambda x: int(x)),
            nbinsx=20,
            marker_color="#0066FF",
            opacity=0.75,
        ))
        fig_time.update_layout(
            title="论文时间分布直方图",
            xaxis_title="年份",
            yaxis_title="论文数量",
        )
        st.plotly_chart(fig_time, use_container_width=True)

    # ─── Tab3：关键词自引 ─────────────────────────────────────────────────────
    with tab3:
        st.markdown("#### 关键词自引偏差（高频重叠关键词）")
        st.markdown("以下关键词在超过50%的文件中重复出现，可能形成认知回音壁：")
        self_bias = _detect_keyword_self_bias(files)
        if self_bias:
            kw_df = pd.DataFrame(self_bias, columns=["关键词", "覆盖文件数"])
            kw_df["覆盖率"] = kw_df["覆盖文件数"].apply(lambda x: f"{x/len(files):.0%}")
            st.dataframe(kw_df, use_container_width=True)

            fig_kw = go.Figure(go.Bar(
                x=[k for k, _ in self_bias],
                y=[c for _, c in self_bias],
                marker_color="#FF6600",
            ))
            fig_kw.update_layout(title="高频重叠关键词分布", xaxis_title="关键词", yaxis_title="出现文件数")
            st.plotly_chart(fig_kw, use_container_width=True)
        else:
            st.success("✅ 未发现显著的关键词自引偏差")

    st.markdown("---")
    if st.button("🧠 AI综合偏差诊断报告", key="bias_ai"):
        over_str = ", ".join(bias_df[bias_df["偏差系数"] > 0.3]["国家/地区"].tolist()) or "无"
        self_str = ", ".join(k for k, _ in self_bias[:5]) if self_bias else "无"
        prompt = (
            f"对以下学术论文库的引用偏差进行综合诊断：\n"
            f"- 地理过度引用：{over_str}\n"
            f"- 时间偏向：{temp_bias['偏向']}\n"
            f"- 高频自引关键词：{self_str}\n"
            f"- 总文件数：{len(files)}\n"
            "请给出：偏差的潜在原因、对研究质量的影响评估、以及改进建议（包括应补充哪些地区/年代/主题的文献）。"
        )
        stream_ai_assistant(prompt, **_llm_kwargs(ctx))

    import json
    render_sge_export_ui(
        mode_id="mode6",
        mode_name="引用偏差探测报告",
        intel_lines={
            "时间偏向": temp_bias["偏向"],
            "近期化率": temp_bias["近期化率"],
            "高频自引词数": len(self_bias),
        },
        snapshots={
            "geo_bias.json": json.dumps(bias_df.to_dict(orient="records"), ensure_ascii=False),
            "temporal_bias.json": json.dumps(temp_bias, ensure_ascii=False),
            "keyword_self_bias.json": json.dumps(self_bias, ensure_ascii=False),
        },
        inventory_files=files,
    )


def _llm_kwargs(ctx):
    return {k: ctx[k] for k in ("llm_mode", "selected_model_path", "base_url", "api_key", "model")}
