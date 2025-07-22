# from __future__ import annotations

# from dataclasses import dataclass, field

# from langgraph.graph import add_messages
# from typing_extensions import Annotated


# import operator
# from dataclasses import dataclass, field
# from typing_extensions import Annotated
from typing import List, Dict, TypedDict


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
    analysis_results: List[dict]
    
    # Populated by the worker after aggregating all chunks
    top_5_positive_topics: List[str]
    top_5_negative_topics: List[str]

    # Populated by the topic_summary_node
    topic_summaries: Dict[str, str]  # Maps topic to summary text
    
    # Populated by `enrich_and_summarize_topics_node`
    summary_context: dict
    
    # The final output from `generate_final_report_node`
    summary: str