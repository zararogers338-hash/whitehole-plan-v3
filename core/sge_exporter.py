# -*- coding: utf-8 -*-
"""SGE 黑盒导出工具——统一封装 ZIP 打包与 pywebview JS 注入。"""

import io
import json
import base64
import zipfile
import datetime

import streamlit as st


def _now_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")


def _now_stamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def build_sge_zip(
    mode_name: str,
    intel_lines: dict,
    snapshots: dict[str, bytes | str],
    inventory_files: list | None = None,
) -> bytes:
    """
    构建 SGE ZIP 字节流。

    Args:
        mode_name:        模式名称，写入 MANIFEST [TARGET]
        intel_lines:      情报字典，写入 MANIFEST [INTEL]
        snapshots:        文件名->内容映射，写入 SNAPSHOTS/ 目录
        inventory_files:  上传文件列表（取文件名），写入 MANIFEST [INVENTORY]
    Returns:
        ZIP 的原始字节
    """
    inventory = "\n".join(
        f"- {f.name}" for f in (inventory_files or [])
    ) or "（无）"

    intel_block = "\n".join(f"{k}：{v}" for k, v in intel_lines.items())

    manifest = f"""# SGE 格式工程规范 v1.2 [白洞计划 v3.0]

[TARGET]
{mode_name}

[INVENTORY]
{inventory}

[ORIGIN]
白洞计划 v3.0 本地模拟器 - {_now_str()}

[INTEL]
{intel_block}
"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("MANIFEST.TXT", manifest)
        for fname, content in snapshots.items():
            path = f"SNAPSHOTS/{fname}"
            if isinstance(content, str):
                zf.writestr(path, content)
            else:
                zf.writestr(path, content)
    buf.seek(0)
    return buf.read()


def render_sge_export_ui(
    mode_id: str,
    mode_name: str,
    intel_lines: dict,
    snapshots: dict[str, bytes | str],
    inventory_files: list | None = None,
):
    """
    在 Streamlit 中渲染 SGE 导出 expander。
    自动处理 pywebview 注入 + 异常提示。
    """
    with st.expander("📦 导出为 SGE 黑盒文件（当前视图）", expanded=False):
        st.markdown("生成密封 SGE 黑盒：包含战术简报 + 全量快照数据。")
        st.markdown(
            '**点击后会弹出系统保存对话框，默认打开"下载"文件夹。**'
        )

        filename = f"whitehole_{mode_id}_{_now_stamp()}.sge"

        if st.button("💾 导出 SGE 文件（选择保存位置）", key=f"sge_btn_{mode_id}"):
            raw = build_sge_zip(mode_name, intel_lines, snapshots, inventory_files)
            b64 = base64.b64encode(raw).decode("utf-8")
            _inject_save_script(b64, filename, mode_id)


def _inject_save_script(b64_data: str, filename: str, key: str):
    """向 Streamlit 注入 pywebview 保存对话框调用脚本。"""
    script = f"""
<script type="text/javascript">
(function() {{
    function doSave() {{
        if (typeof pywebview === 'undefined') {{
            alert("pywebview 未加载！如果你在浏览器中直接运行，请改用 main.py 启动。");
            return;
        }}
        pywebview.ready.then(function() {{
            window.pywebview.api.save_sge("{b64_data}", "{filename}")
                .then(function(resp) {{
                    if (resp.status === "success") {{
                        alert("✅ SGE 文件已保存到：\\n" + resp.path);
                    }} else if (resp.status === "cancelled") {{
                        console.log("用户取消了保存");
                    }} else {{
                        alert("❌ 保存出错：" + resp.message);
                    }}
                }})
                .catch(function(err) {{
                    alert("❌ API 调用失败：" + err.message);
                }});
        }}).catch(function(err) {{
            alert("❌ pywebview.ready 超时：" + err);
        }});
    }}
    doSave();
}})();
</script>
"""
    st.markdown(script, unsafe_allow_html=True)
    st.info("正在唤起系统保存对话框……（如未弹出，请查看控制台调试输出）")
