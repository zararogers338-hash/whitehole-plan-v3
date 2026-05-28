# -*- coding: utf-8 -*-
"""全局配置、常量、枚举"""

APP_TITLE = "白洞计划 v3.0 - 学术命运模拟器"
APP_VERSION = "3.0.0"

SYSTEM_PROMPT = (
    "你是一个白洞计划学术命运模拟器专家，精通学术场域分析、趋势预测、"
    "干预模拟和全球共识研究。用流畅、自然的中文回复，语言专业但易懂，"
    "避免英文术语或生硬翻译。直接给出分析报告，不要寒暄。"
)

MODES = [
    "1. 个人学术命运轨迹",
    "2. 实时趋势预测 + 未来论文生成器",
    "3. 反向干预模拟器",
    "4. 多场域对比 + 跨学科移植",
    "5. 社区共治 + 全球实时共识地图",
    "6. 引用偏差探测器",
    "7. 跨学科移植风险模拟器",
    "8. 审稿AI滥用检测器",
    "9. 重复研究预警系统",
    "10. 隐私匿名共识地图",
]

STOPWORDS = {
    '的', '了', '在', '是', '和', '与', '等', '为', '对', '于', '中', '有',
    '以', '从', '到', '由', '及', '一个', '这种', '通过', '可以', '我们',
    '研究', '基于', '提出', '使用', '进行', '分析', '结果', '方法', '系统',
    '模型', '数据', '应用', '本文',
}

COUNTRY_KEYWORDS: dict[str, list[str]] = {
    "中国": [
        "china", "chinese", "beijing", "shanghai", "tsinghua", "peking",
        "cas", "cnic", "huawei", "zhongguo",
    ],
    "美国": [
        "usa", "united states", "america", "stanford", "mit", "harvard",
        "berkeley", "california", "new york", "nasa", "google", "microsoft",
    ],
    "欧洲": [
        "europe", "uk", "united kingdom", "germany", "france", "oxford",
        "cambridge", "eth zurich", "max planck", "cern", "esa",
    ],
    "其他": [],
}

# 号角图外观
HORN_LINE_COLOR = "#0066FF"
HORN_LINE_WIDTH = 10

# Streamlit server 启动最大等待秒数
STREAMLIT_START_TIMEOUT = 90
