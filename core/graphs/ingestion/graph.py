from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from core.graphs.ingestion.nodes.chunk_document import chunk_document
from core.graphs.ingestion.nodes.embed_document import embed_document
from core.graphs.ingestion.nodes.identify_item_name import identify_item_name
from core.graphs.ingestion.nodes.parse_document import parse_document
from core.graphs.ingestion.nodes.summarize_images import summarize_images
from core.graphs.ingestion.nodes.upload_images import upload_images
from core.graphs.ingestion.nodes.validate_request import validate_request
from core.graphs.ingestion.state import IngestionState


def build_ingestion_graph() -> CompiledStateGraph:
    builder = StateGraph(IngestionState)
    builder.add_node("validate_request", validate_request)
    builder.add_node("parse_document", parse_document)
    builder.add_node("summarize_images", summarize_images)
    builder.add_node("upload_images", upload_images)
    builder.add_node("chunk_document", chunk_document)
    builder.add_node("identify_item_name", identify_item_name)
    builder.add_node("embed_document", embed_document)

    builder.add_edge(START, "validate_request")
    builder.add_edge("validate_request", "parse_document")
    builder.add_edge("parse_document", "summarize_images")
    builder.add_edge("summarize_images", "upload_images")
    builder.add_edge("upload_images", "chunk_document")
    builder.add_edge("chunk_document", "identify_item_name")
    builder.add_edge("identify_item_name", "embed_document")
    builder.add_edge("embed_document", END)

    return builder.compile()
