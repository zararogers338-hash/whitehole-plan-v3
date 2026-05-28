# -*- coding: utf-8 -*-
"""pywebview JS ↔ Python 桥接 API。"""

import os
import base64

import webview


class Api:
    """暴露给前端 JS 的 Python API 对象。"""

    def save_sge(self, b64_data: str, filename: str) -> dict:
        """弹出系统保存对话框并将 base64 数据写入选定路径。"""
        try:
            data = base64.b64decode(b64_data)
            downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            directory = downloads if os.path.exists(downloads) else os.path.expanduser("~")

            result = webview.windows[0].create_file_dialog(
                webview.SAVE_DIALOG,
                directory=directory,
                save_filename=filename,
                file_types=("SGE Files (*.sge)", "ZIP Files (*.zip)", "All Files (*.*)"),
            )
            if result:
                with open(result, "wb") as f:
                    f.write(data)
                return {"status": "success", "path": str(result)}
            return {"status": "cancelled"}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}
