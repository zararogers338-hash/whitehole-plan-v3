# -*- coding: utf-8 -*-
"""文本处理工具：文件解析、关键词提取、国家识别、时间提取"""

import re
import hashlib
from collections import Counter

import streamlit as st

from core.config import STOPWORDS, COUNTRY_KEYWORDS


# ─── 文件解析 ────────────────────────────────────────────────────────────────

def extract_text_from_file(file) -> str:
    """从 PDF / DOCX / TXT / MD 文件对象中提取纯文本。"""
    name = file.name.lower()
    try:
        if name.endswith(".pdf"):
            from PyPDF2 import PdfReader
            reader = PdfReader(file)
            return "".join(page.extract_text() or "" for page in reader.pages)
        elif name.endswith(".docx"):
            import docx as _docx
            doc = _docx.Document(file)
            return "\n".join(para.text for para in doc.paragraphs)
        else:
            return file.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        st.warning(f"文件 {file.name} 提取失败：{exc}")
        return ""


# ─── 关键词 ──────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def extract_keywords(text: str, top_n: int = 15) -> list[tuple[str, float]]:
    """用 jieba TF-IDF 提取关键词并过滤停用词。"""
    import jieba.analyse  # lazy import 避免启动慢
    tags = jieba.analyse.extract_tags(text, topK=top_n * 2, withWeight=True)
    return [(t, w) for t, w in tags if t not in STOPWORDS][:top_n]


# ─── 国家识别 ─────────────────────────────────────────────────────────────────

def get_country(text: str, name: str) -> str:
    """从文本中推断论文所属国家/地区。"""
    lower = re.sub(r"download.*|arxiv.*|github.*|pdf.*|\d+", "",
                   (text + " " + name).lower())
    scores: dict[str, int] = {k: 0 for k in COUNTRY_KEYWORDS if k != "其他"}
    for country, kws in COUNTRY_KEYWORDS.items():
        if country == "其他":
            continue
        for kw in kws:
            if kw in lower:
                scores[country] += 1
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return best if scores[best] > 0 else "未知"


# ─── 时间提取 ─────────────────────────────────────────────────────────────────

def extract_time_decimal(name: str, text: str = "") -> float:
    """从文件名或正文中提取年份，返回带随机小数偏移的时间值（用于三维散点）。"""
    m = re.search(r"(19\d{2}|20\d{2})", name)
    if m:
        year = int(m.group(1))
    else:
        years = re.findall(r"\b(19\d{2}|20\d{2})\b", text)
        year = int(Counter(years).most_common(1)[0][0]) if years else 2024
    h = int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)
    return year + (h % 1000) / 1000.0


# ─── 批量构建 DataFrame ───────────────────────────────────────────────────────

def build_library_df(files: list) -> "pd.DataFrame":
    """将上传文件列表转换为含 name/short_name/time/text/country 的 DataFrame。"""
    import pandas as pd
    rows = []
    for file in files:
        text = extract_text_from_file(file)
        name = file.name
        rows.append({
            "name": name,
            "short_name": name[:18] + "…" if len(name) > 18 else name,
            "time": extract_time_decimal(name, text),
            "text": text,
            "country": get_country(text, name),
        })
    return pd.DataFrame(rows)
