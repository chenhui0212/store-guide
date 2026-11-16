from typing import TypedDict, List, Required


class IngestionState(TypedDict, total=False):
    """导入流程图状态"""

    task_id: str

    file_path: Required[str]

    # ===== 文件信息 =====

    file_title: str

    item_name: str

    # ===== 中间数据 =====

    markdown_content: str

    chunks: List
