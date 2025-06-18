# from __future__ import annotations

# from dataclasses import dataclass, field

# from langgraph.graph import add_messages
# from typing_extensions import Annotated


# import operator
# from dataclasses import dataclass, field
# from typing_extensions import Annotated
from typing import List, TypedDict


# class OverallState(TypedDict):
#     messages: Annotated[list, add_messages]
#     search_query: Annotated[list, operator.add]
#     web_research_result: Annotated[list, operator.add]
#     sources_gathered: Annotated[list, operator.add]
#     initial_search_query_count: int
#     max_research_loops: int
#     research_loop_count: int
#     reasoning_model: str


# class ReflectionState(TypedDict):
#     is_sufficient: bool
#     knowledge_gap: str
#     follow_up_queries: Annotated[list, operator.add]
#     research_loop_count: int
#     number_of_ran_queries: int


# class Query(TypedDict):
#     query: str
#     rationale: str


# class QueryGenerationState(TypedDict):
#     query_list: list[Query]


# class WebSearchState(TypedDict):
#     search_query: str
#     id: str


# @dataclass(kw_only=True)
# class SearchStateOutput:
#     running_summary: str = field(default=None)  # Final report


class AgentState(TypedDict):
    """
    Defines the state or "memory" of our feedback analysis agent.
    This dictionary-like object is passed between each node in the graph.
    """
    
    # Initial input
    product_id: str

    # Populated by the first node
    reviews: List[dict]

    # --- Temporary fields for parallel branches ---
    # Each parallel node will write to its own unique key to avoid conflicts.
    sentiment_outputs: List[dict]
    topic_outputs: List[dict]
    
    # --- Final combined results ---
    # A later "joiner" node will combine the above outputs into this final structure.
    analysis_results: List[dict]
    summary: str