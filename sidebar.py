# -*- coding: utf-8 -*-
"""侧边栏渲染与状态返回。"""

import json
import zipfile

import streamlit as st

from core.config import MODES
from api.llm_client import scan_gguf_models


def render_sidebar() -> dict:
    """
    渲染完整侧边栏，返回运行时上下文字典：
      files1, files2, mode,
      llm_mode, selected_model_path, base_url, api_key, model
    """
    ctx: dict = {}

    with st.sidebar:
        st.header("📄 数据加载")

        st.subheader("数据集1（主场域）")
        files1 = st.file_uploader(
            "上传文件1",
            type=["pdf", "txt", "docx", "md"],
            accept_multiple_files=True,
            key="files1",
        )
        st.subheader("数据集2（对比/移植）")
        files2 = st.file_uploader(
            "上传文件2",
            type=["pdf", "txt", "docx", "md"],
            accept_multiple_files=True,
            key="files2",
        )

        col1, col2 = st.columns(2)
        col1.metric("数据集1", len(files1) if files1 else 0, "篇")
        col2.metric("数据集2", len(files2) if files2 else 0, "篇")

        st.header("🛡️ 功能模式")
        mode = st.radio("选择功能", MODES, key="mode_radio")

        # ─── LLM 设置 ────────────────────────────────────────────────────────
        with st.expander("🤖 LLM 引擎设置", expanded=False):
            llm_mode = st.radio(
                "选择 LLM 模式",
                ["内置本地模型（推荐）", "自定义API（Groq/OpenAI 等）"],
                key="llm_mode",
            )

            selected_model_path: str | None = None
            base_url = "https://api.groq.com/openai"
            api_key = ""
            model = "llama3-70b-8192"

            if llm_mode == "内置本地模型（推荐）":
                available = scan_gguf_models()
                if available:
                    names = [m[0] for m in available]
                    paths = dict(available)
                    sel = st.selectbox("选择内置模型", names, index=0, key="model_select")
                    selected_model_path = paths[sel]
                    st.success(f"✅ {sel}（本地运行，免费私有）")
                else:
                    st.warning("models/ 目录未检测到 GGUF 模型文件")
            else:
                base_url = st.text_input("API Base URL", value=base_url, key="api_url")
                api_key = st.text_input("API Key", type="password", key="api_key")
                model = st.text_input("模型名", value=model, key="model_name")

        ctx["llm_mode"] = llm_mode
        ctx["selected_model_path"] = selected_model_path
        ctx["base_url"] = base_url
        ctx["api_key"] = api_key
        ctx["model"] = model

        # ─── SGE 导入 ─────────────────────────────────────────────────────────
        st.header("📦 SGE 黑盒管理")
        sge_file = st.file_uploader(
            "导入并查看 SGE 文件", type=["zip", "sge"], key="sge_import"
        )
        if sge_file is not None:
            _render_sge_viewer(sge_file)

    ctx["files1"] = files1 or []
    ctx["files2"] = files2 or []
    ctx["mode"] = mode
    return ctx


def _render_sge_viewer(sge_file):
    try:
        with zipfile.ZipFile(sge_file) as zf:
            namelist = zf.namelist()
            if "MANIFEST.TXT" not in namelist:
                st.error("无效 SGE 文件：缺少 MANIFEST.TXT")
                return
            st.subheader("📜 战术简报")
            st.text(zf.read("MANIFEST.TXT").decode("utf-8"))

            st.subheader("🔒 快照区")
            for item in namelist:
                if not item.startswith("SNAPSHOTS/") or item.endswith("/"):
                    continue
                data = zf.read(item)
                base = item.split("/")[-1]
                if item.endswith(".html"):
                    st.markdown(f"**{base}**（交互视图）")
                    st.components.v1.html(data.decode("utf-8"), height=700, scrolling=True)
                elif item.endswith(".png"):
                    st.image(data, caption=base)
                elif item.endswith(".json"):
                    st.markdown(f"**{base}**")
                    st.json(json.loads(data))
                elif item.endswith(".txt"):
                    st.markdown(f"**{base}**")
                    st.text(data.decode("utf-8"))
                else:
                    st.download_button(f"下载 {base}", data, file_name=base)
    except Exception as exc:
        st.error(f"无法读取 SGE 文件：{exc}")
