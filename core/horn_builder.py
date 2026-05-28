# -*- coding: utf-8 -*-
"""号角（螺旋锥）图形构建器——所有模式共用，消除重复代码。"""

import numpy as np
import plotly.graph_objects as go

from core.config import HORN_LINE_COLOR, HORN_LINE_WIDTH


def _horn_spine(t_min: float, t_max: float, extra: float = 0.0, n: int = 200):
    """计算号角脊线的 x/y/z 坐标。"""
    theta = np.linspace(0, 2 * np.pi, n)
    z = np.linspace(t_min, t_max + extra, n)
    span = t_max - t_min + extra + 1e-6
    r = 1.0 + 0.8 * np.exp((z - t_min) / span)
    return r * np.cos(theta), r * np.sin(theta), z


def build_horn_figure(
    t_min: float,
    t_max: float,
    extra: float = 0.0,
) -> go.Figure:
    """
    构建基础号角骨架图（只含脊线，不含数据点）。
    extra: z 轴额外延伸量（模式4/5 用 3.0）
    """
    x, y, z = _horn_spine(t_min, t_max, extra)
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z,
        mode="lines",
        line=dict(color=HORN_LINE_COLOR, width=HORN_LINE_WIDTH),
        name="学术场域脊线",
        showlegend=False,
    ))
    return fig


def scatter_on_horn(
    fig: go.Figure,
    times: "np.ndarray",
    labels: list[str],
    t_min: float,
    t_max: float,
    extra: float = 0.0,
    color: str = "#00AAFF",
    size: int = 8,
    symbol: str = "circle",
    name: str = "",
    seed: int | None = None,
) -> go.Figure:
    """
    在号角面上按时间值散布数据点。
    每个点的角度用标签名哈希固定（seed=None 时随机）。
    """
    span = t_max - t_min + extra + 1e-6
    norm = (times - t_min) / span
    r = 1.0 + 0.8 * np.exp(norm)

    rng = np.random.default_rng(seed)
    theta = rng.uniform(0, 2 * np.pi, len(times))

    fig.add_trace(go.Scatter3d(
        x=r * np.cos(theta),
        y=r * np.sin(theta),
        z=times,
        mode="markers+text",
        marker=dict(size=size, color=color, symbol=symbol, opacity=0.85),
        text=labels,
        textposition="top center",
        name=name,
    ))
    return fig


def highlight_on_horn(
    fig: go.Figure,
    time_val: float,
    label: str,
    t_min: float,
    t_max: float,
    extra: float = 0.0,
    color: str = "red",
    size: int = 20,
    symbol: str = "diamond",
) -> go.Figure:
    """用固定哈希角度高亮单个点（用于模式1选中论文）。"""
    span = t_max - t_min + extra + 1e-6
    norm = (time_val - t_min) / span
    r = 1.0 + 0.8 * np.exp(norm)
    theta = int(hashlib.sha256(label.encode()).hexdigest()[:8], 16) % 360 / 180 * np.pi

    fig.add_trace(go.Scatter3d(
        x=[r * np.cos(theta)],
        y=[r * np.sin(theta)],
        z=[time_val],
        mode="markers+text",
        marker=dict(size=size, color=color, symbol=symbol),
        text=[label[:20]],
        textposition="top center",
        name="选中论文",
    ))
    return fig


def apply_horn_layout(fig: go.Figure, height: int = 800) -> go.Figure:
    """统一设置号角图布局。"""
    fig.update_layout(
        scene=dict(
            xaxis_visible=False,
            yaxis_visible=False,
            zaxis_visible=False,
            dragmode="orbit",
        ),
        height=height,
        margin=dict(l=0, r=0, t=30, b=0),
    )
    return fig


import hashlib  # noqa: E402 (置于底部以避免循环)
