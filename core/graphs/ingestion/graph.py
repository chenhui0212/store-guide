from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from core.graphs.ingestion.nodes.parse_document import parse_document
from core.graphs.ingestion.nodes.validate_request import validate_request
from .state import IngestionState


def build_ingestion_graph() -> CompiledStateGraph:
    builder = StateGraph(IngestionState)
    builder.add_node("validate_request", validate_request)
    builder.add_node("parse_document", parse_document)

    builder.add_edge(START, "validate_request")
    builder.add_edge("validate_request", "parse_document")
    builder.add_edge("parse_document", END)

    return builder.compile()
