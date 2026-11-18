from pathlib import Path

from core.callbacks.node_logging import NodeLoggingCallback
from core.graphs.ingestion.graph import build_ingestion_graph


def test_ingestion_graph_with_pdf():
    """测试解析 PDF 文件"""
    file_name = "H3C LA2608室内无线网关 用户手册.pdf"
    pdf_path = Path(__file__).resolve().parents[1] / "fixtures" / file_name

    graph = build_ingestion_graph()
    state = {"file_path": str(pdf_path)}
    result = graph.invoke(state, config={"callbacks": [NodeLoggingCallback()]})

    assert "H3C LA2608 室内无线网关" in result["markdown_content"]
