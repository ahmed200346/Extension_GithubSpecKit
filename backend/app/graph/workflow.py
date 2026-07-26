# app/graph/workflow.py
from langgraph.graph import StateGraph, START, END
from app.graph.state import GraphState
from app.graph.nodes import (
    parsing_node, 
    summary_node, 
    glossary_node, 
    diagram_node,
    doc_writer_node,
    layout_node
)

def create_pipeline_workflow():
    """
    Assemble le workflow LangGraph avec orchestration multi-agents et publication PDF finale.
    
                 [START]
                    │
              [parsing_agent]
                ┌───┼───┐  (Trifurcation parallèle)
                ▼   ▼   ▼
          [summary] [glossary] [diagram]
                └───┼───┘  (Convergence)
                    ▼
            [doc_writer_agent]
                    │
             [layout_agent]
                    │
                  [END]
    """
    workflow = StateGraph(GraphState)
    
    # 1. Ajout des Nœuds
    workflow.add_node("parsing_agent", parsing_node)
    workflow.add_node("summary_agent", summary_node)
    workflow.add_node("glossary_agent", glossary_node)
    workflow.add_node("diagram_agent", diagram_node)
    workflow.add_node("doc_writer_agent", doc_writer_node)
    workflow.add_node("layout_agent", layout_node)
    
    # 2. Edges
    workflow.add_edge(START, "parsing_agent")
    
    # Parallélisation
    workflow.add_edge("parsing_agent", "summary_agent")
    workflow.add_edge("parsing_agent", "glossary_agent")
    workflow.add_edge("parsing_agent", "diagram_agent")
    
    # Convergence vers DocWriter
    workflow.add_edge("summary_agent", "doc_writer_agent")
    workflow.add_edge("glossary_agent", "doc_writer_agent")
    workflow.add_edge("diagram_agent", "doc_writer_agent")
    
    # Séquence finale : DocWriter -> Layout -> END
    workflow.add_edge("doc_writer_agent", "layout_agent")
    workflow.add_edge("layout_agent", END)
    
    return workflow.compile()
