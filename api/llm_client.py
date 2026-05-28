# -*- coding: utf-8 -*-
"""
LLM 推理客户端。
修复：
  - SSE [DONE] 终止符未过滤导致的 JSONDecodeError
  - stream_ai_assistant 依赖全局变量改为显式参数传入
  - load_local_llm 使用 @st.cache_resource 正确缓存
"""

import json
import os

import requests
import streamlit as st

from core.config import SYSTEM_PROMPT


def scan_gguf_models(model_dir: str = "models") -> list[tuple[str, str]]:
    """扫描 models/ 目录，返回 (文件名, 完整路径) 列表，按大小降序排序。"""
    if not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)
        return []
    models = [
        (f, os.path.join(model_dir, f))
        for f in os.listdir(model_dir)
        if f.lower().endswith(".gguf")
    ]
    models.sort(key=lambda x: os.path.getsize(x[1]), reverse=True)
    return models


@st.cache_resource(show_spinner="正在加载本地模型…")
def load_local_llm(model_path: str):
    """加载 llama-cpp 模型，失败时返回 None。"""
    if not os.path.exists(model_path):
        return None
    try:
        from llama_cpp import Llama
        return Llama(
            model_path=model_path,
            n_ctx=8192,
            n_threads=8,
            n_gpu_layers=-1,
            verbose=False,
        )
    except Exception as exc:
        st.warning(f"模型加载失败：{str(exc)[:120]}")
        return None


def stream_ai_assistant(
    prompt: str,
    llm_mode: str,
    selected_model_path: str | None,
    base_url: str,
    api_key: str,
    model: str,
) -> str:
    """
    流式调用 LLM，在 Streamlit chat_message 中实时渲染输出。

    Args:
        prompt:             用户提示词
        llm_mode:           "内置本地模型（推荐）" 或 "自定义API"
        selected_model_path: 本地 GGUF 路径
        base_url:           API base URL
        api_key:            API 密钥
        model:              模型名称
    Returns:
        完整生成文本
    """
    full_text = ""
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("**AI 顾问正在分析学术场域…**")
        try:
            if llm_mode == "内置本地模型（推荐）" and selected_model_path:
                full_text = _stream_local(
                    prompt, selected_model_path, placeholder
                )
            else:
                full_text = _stream_api(
                    prompt, base_url, api_key, model, placeholder
                )
        except Exception as exc:
            placeholder.markdown(full_text + f"\n\n⚠️ 生成中断：{str(exc)[:100]}")
    return full_text


# ─── 内部函数 ─────────────────────────────────────────────────────────────────

def _stream_local(prompt: str, model_path: str, placeholder) -> str:
    llm = load_local_llm(model_path)
    if not llm:
        placeholder.markdown("⚠️ 模型未加载，请检查 models/ 目录")
        return ""
    full = ""
    formatted = SYSTEM_PROMPT + "\n\n" + prompt
    for chunk in llm(formatted, stream=True, max_tokens=1500, temperature=0.8):
        token = chunk["choices"][0]["text"]
        full += token
        placeholder.markdown(full + "▎")
    placeholder.markdown(full)
    return full


def _stream_api(
    prompt: str,
    base_url: str,
    api_key: str,
    model: str,
    placeholder,
) -> str:
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": SYSTEM_PROMPT + "\n\n" + prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 1500,
        "stream": True,
    }
    resp = requests.post(url, headers=headers, json=payload, stream=True, timeout=90)
    resp.raise_for_status()

    full = ""
    for raw_line in resp.iter_lines():
        if not raw_line:
            continue
        line = raw_line.decode("utf-8")
        if not line.startswith("data: "):
            continue
        payload_str = line[6:].strip()
        # ✅ 修复：[DONE] 是流式结束信号，不是 JSON，必须跳过
        if payload_str == "[DONE]":
            break
        try:
            chunk = json.loads(payload_str)
        except json.JSONDecodeError:
            continue
        delta = chunk.get("choices", [{}])[0].get("delta", {})
        content = delta.get("content")
        if content:
            full += content
            placeholder.markdown(full + "▎")

    placeholder.markdown(full)
    return full
