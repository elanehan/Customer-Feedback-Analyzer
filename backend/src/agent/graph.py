import os

# from agent.tools_and_schemas import SearchQueryList, Reflection
from dotenv import load_dotenv
# from langchain_core.messages import AIMessage
# from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import START, END
# from langchain_core.runnables import RunnableConfig
# from google.genai import Client

import json
from collections import Counter
from typing import List
import time

from langchain_core.prompts import PromptTemplate
from agent.state import AgentState
from agent.tools_and_schemas import get_reviews_from_bigquery
from agent.prompts import batch_analysis_prompt_template, normalize_topics_prompt_template, topic_summary_prompt_template, executive_summary_prompt_template
from agent.utils import parse_llm_json_output, json_serial

# from agent.state import (
#     OverallState,
#     QueryGenerationState,
#     ReflectionState,
#     WebSearchState,
# )
from agent.configuration import AgentConfig
# from agent.prompts import (
#     get_current_date,
#     query_writer_instructions,
#     web_searcher_instructions,
#     reflection_instructions,
#     answer_instructions,
# )
from langchain_google_genai import ChatGoogleGenerativeAI
# from agent.utils import (
#     get_citations,
#     get_research_topic,
#     insert_citation_markers,
#     resolve_urls,
# )

# load_dotenv()

# if os.getenv("GEMINI_API_KEY") is None:
#     raise ValueError("GEMINI_API_KEY is not set")

# # Used for Google Search API
# genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))


# # Nodes
# def generate_query(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
#     """LangGraph node that generates a search queries based on the User's question.

#     Uses Gemini 2.0 Flash to create an optimized search query for web research based on
#     the User's question.

#     Args:
#         state: Current graph state containing the User's question
#         config: Configuration for the runnable, including LLM provider settings

#     Returns:
#         Dictionary with state update, including search_query key containing the generated query
#     """
#     configurable = Configuration.from_runnable_config(config)

#     # check for custom initial search query count
#     if state.get("initial_search_query_count") is None:
#         state["initial_search_query_count"] = configurable.number_of_initial_queries

#     # init Gemini 2.0 Flash
#     llm = ChatGoogleGenerativeAI(
#         model=configurable.query_generator_model,
#         temperature=1.0,
#         max_retries=2,
#         api_key=os.getenv("GEMINI_API_KEY"),
#     )
#     structured_llm = llm.with_structured_output(SearchQueryList)

#     # Format the prompt
#     current_date = get_current_date()
#     formatted_prompt = query_writer_instructions.format(
#         current_date=current_date,
#         research_topic=get_research_topic(state["messages"]),
#         number_queries=state["initial_search_query_count"],
#     )
#     # Generate the search queries
#     result = structured_llm.invoke(formatted_prompt)
#     return {"query_list": result.query}


# def continue_to_web_research(state: QueryGenerationState):
#     """LangGraph node that sends the search queries to the web research node.

#     This is used to spawn n number of web research nodes, one for each search query.
#     """
#     return [
#         Send("web_research", {"search_query": search_query, "id": int(idx)})
#         for idx, search_query in enumerate(state["query_list"])
#     ]


# def web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
#     """LangGraph node that performs web research using the native Google Search API tool.

#     Executes a web search using the native Google Search API tool in combination with Gemini 2.0 Flash.

#     Args:
#         state: Current graph state containing the search query and research loop count
#         config: Configuration for the runnable, including search API settings

#     Returns:
#         Dictionary with state update, including sources_gathered, research_loop_count, and web_research_results
#     """
#     # Configure
#     configurable = Configuration.from_runnable_config(config)
#     formatted_prompt = web_searcher_instructions.format(
#         current_date=get_current_date(),
#         research_topic=state["search_query"],
#     )

#     # Uses the google genai client as the langchain client doesn't return grounding metadata
#     response = genai_client.models.generate_content(
#         model=configurable.query_generator_model,
#         contents=formatted_prompt,
#         config={
#             "tools": [{"google_search": {}}],
#             "temperature": 0,
#         },
#     )
#     # resolve the urls to short urls for saving tokens and time
#     resolved_urls = resolve_urls(
#         response.candidates[0].grounding_metadata.grounding_chunks, state["id"]
#     )
#     # Gets the citations and adds them to the generated text
#     citations = get_citations(response, resolved_urls)
#     modified_text = insert_citation_markers(response.text, citations)
#     sources_gathered = [item for citation in citations for item in citation["segments"]]

#     return {
#         "sources_gathered": sources_gathered,
#         "search_query": [state["search_query"]],
#         "web_research_result": [modified_text],
#     }


# def reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
#     """LangGraph node that identifies knowledge gaps and generates potential follow-up queries.

#     Analyzes the current summary to identify areas for further research and generates
#     potential follow-up queries. Uses structured output to extract
#     the follow-up query in JSON format.

#     Args:
#         state: Current graph state containing the running summary and research topic
#         config: Configuration for the runnable, including LLM provider settings

#     Returns:
#         Dictionary with state update, including search_query key containing the generated follow-up query
#     """
#     configurable = Configuration.from_runnable_config(config)
#     # Increment the research loop count and get the reasoning model
#     state["research_loop_count"] = state.get("research_loop_count", 0) + 1
#     reasoning_model = state.get("reasoning_model") or configurable.reasoning_model

#     # Format the prompt
#     current_date = get_current_date()
#     formatted_prompt = reflection_instructions.format(
#         current_date=current_date,
#         research_topic=get_research_topic(state["messages"]),
#         summaries="\n\n---\n\n".join(state["web_research_result"]),
#     )
#     # init Reasoning Model
#     llm = ChatGoogleGenerativeAI(
#         model=reasoning_model,
#         temperature=1.0,
#         max_retries=2,
#         api_key=os.getenv("GEMINI_API_KEY"),
#     )
#     result = llm.with_structured_output(Reflection).invoke(formatted_prompt)

#     return {
#         "is_sufficient": result.is_sufficient,
#         "knowledge_gap": result.knowledge_gap,
#         "follow_up_queries": result.follow_up_queries,
#         "research_loop_count": state["research_loop_count"],
#         "number_of_ran_queries": len(state["search_query"]),
#     }


# def evaluate_research(
#     state: ReflectionState,
#     config: RunnableConfig,
# ) -> OverallState:
#     """LangGraph routing function that determines the next step in the research flow.

#     Controls the research loop by deciding whether to continue gathering information
#     or to finalize the summary based on the configured maximum number of research loops.

#     Args:
#         state: Current graph state containing the research loop count
#         config: Configuration for the runnable, including max_research_loops setting

#     Returns:
#         String literal indicating the next node to visit ("web_research" or "finalize_summary")
#     """
#     configurable = Configuration.from_runnable_config(config)
#     max_research_loops = (
#         state.get("max_research_loops")
#         if state.get("max_research_loops") is not None
#         else configurable.max_research_loops
#     )
#     if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
#         return "finalize_answer"
#     else:
#         return [
#             Send(
#                 "web_research",
#                 {
#                     "search_query": follow_up_query,
#                     "id": state["number_of_ran_queries"] + int(idx),
#                 },
#             )
#             for idx, follow_up_query in enumerate(state["follow_up_queries"])
#         ]


# def finalize_answer(state: OverallState, config: RunnableConfig):
#     """LangGraph node that finalizes the research summary.

#     Prepares the final output by deduplicating and formatting sources, then
#     combining them with the running summary to create a well-structured
#     research report with proper citations.

#     Args:
#         state: Current graph state containing the running summary and sources gathered

#     Returns:
#         Dictionary with state update, including running_summary key containing the formatted final summary with sources
#     """
#     configurable = Configuration.from_runnable_config(config)
#     reasoning_model = state.get("reasoning_model") or configurable.reasoning_model

#     # Format the prompt
#     current_date = get_current_date()
#     formatted_prompt = answer_instructions.format(
#         current_date=current_date,
#         research_topic=get_research_topic(state["messages"]),
#         summaries="\n---\n\n".join(state["web_research_result"]),
#     )

#     # init Reasoning Model, default to Gemini 2.5 Flash
#     llm = ChatGoogleGenerativeAI(
#         model=reasoning_model,
#         temperature=0,
#         max_retries=2,
#         api_key=os.getenv("GEMINI_API_KEY"),
#     )
#     result = llm.invoke(formatted_prompt)

#     # Replace the short urls with the original urls and add all used urls to the sources_gathered
#     unique_sources = []
#     for source in state["sources_gathered"]:
#         if source["short_url"] in result.content:
#             result.content = result.content.replace(
#                 source["short_url"], source["value"]
#             )
#             unique_sources.append(source)

#     return {
#         "messages": [AIMessage(content=result.content)],
#         "sources_gathered": unique_sources,
#     }


# # Create our Agent Graph
# builder = StateGraph(OverallState, config_schema=Configuration)

# # Define the nodes we will cycle between
# builder.add_node("generate_query", generate_query)
# builder.add_node("web_research", web_research)
# builder.add_node("reflection", reflection)
# builder.add_node("finalize_answer", finalize_answer)

# # Set the entrypoint as `generate_query`
# # This means that this node is the first one called
# builder.add_edge(START, "generate_query")
# # Add conditional edge to continue with search queries in a parallel branch
# builder.add_conditional_edges(
#     "generate_query", continue_to_web_research, ["web_research"]
# )
# # Reflect on the web research
# builder.add_edge("web_research", "reflection")
# # Evaluate the research
# builder.add_conditional_edges(
#     "reflection", evaluate_research, ["web_research", "finalize_answer"]
# )
# # Finalize the answer
# builder.add_edge("finalize_answer", END)

# graph = builder.compile(name="pro-search-agent")


# --- 1. Load Environment Variables at the Entry Point ---
# This is the first action: load secrets from the .env file into the environment.
print("Loading environment variables...")
load_dotenv()

# --- 3. Validate Secrets and Instantiate Clients (Corrected Version) ---

# Load secrets from the environment
gcp_project_id = os.getenv("GCP_PROJECT_ID")
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Validate that the secrets were actually found. This makes the app "fail fast" with a clear error.
if not gcp_project_id or not gemini_api_key:
    raise ValueError("Required environment variables (GCP_PROJECT_ID, GEMINI_API_KEY) are not set in your .env file.")

# Create a config instance. Since GCP_PROJECT_ID is loaded, we can pass it here.
# Pydantic will validate that it's a string.
try:
    config = AgentConfig(gcp_project_id=gcp_project_id)
    print("Configuration loaded and validated successfully.")
except Exception as e:
    raise ValueError(f"Configuration Error: {e}")

# Instantiate clients, now explicitly passing the API key.
llm = ChatGoogleGenerativeAI(model=config.gemini_model_name, google_api_key=gemini_api_key, temperature=0, max_retries=2)

# --- 4. Define the Node Functions ---
def retrieve_reviews_node(state: AgentState):
    """Fetches reviews from BigQuery using the product_id from the state."""
    print("---NODE: RETRIEVE REVIEWS---")
    product_id = state["product_id"]
    reviews = get_reviews_from_bigquery.invoke({"product_id": product_id})
    return {"reviews": reviews}

def analysis_and_enrichment_node(state: AgentState):
    """
    The single workhorse node that performs all analysis and enrichment.
    """
    print("---NODE: ANALYSIS & ENRICHMENT---")
    reviews = state["reviews"]
    
    # === Step 1: Per-Review Analysis (Batch Call) ===
    review_texts = [r.get("review_text", "") for r in reviews]
    analysis_chain = batch_analysis_prompt_template | llm
    response = analysis_chain.invoke({"review_list_json": json.dumps(review_texts)})
    llm_analyses = parse_llm_json_output(response.content).get("analyses", [])
    
    analysis_results = []
    for i, review in enumerate(reviews):
        analysis_data = llm_analyses[i] if i < len(llm_analyses) else {}
        analysis_results.append({**review, **analysis_data})

    # === Step 2: Topic Normalization ===
    all_raw_topics = [topic for item in analysis_results for topic in item.get('topics', [])]
    unique_topics = sorted(list(set(all_raw_topics)))
    norm_map = {}
    if unique_topics:
        norm_chain = normalize_topics_prompt_template | llm
        norm_response = norm_chain.invoke({"unique_topic_list": json.dumps(unique_topics)})
        norm_map = parse_llm_json_output(norm_response.content)
    
    # Apply the normalization map to the topics
    for item in analysis_results:
        item['topics'] = [norm_map.get(raw_topic, raw_topic) for raw_topic in item.get('topics', [])]

    return {"analysis_results": analysis_results}
    
def topic_summary_node(state: AgentState):
    """
    Generates concise summaries for the top 5 positive and negative topics based on recent reviews.
    """
    print("---NODE: GENERATE TOPIC SUMMARIES---")
    final_analysis_list = state["analysis_results"]
    top_5_positive = state["top_5_positive_topics"]
    top_5_negative = state["top_5_negative_topics"]
    topic_summaries = {}

    # Process positive topics
    for topic in top_5_positive:
        positive_reviews_with_topic = [
            r for r in final_analysis_list
            if topic in r.get('topics', []) and r.get('sentiment') == "Positive"
        ]
        # Take the last 10 reviews for recency
        snippets = [r['review_text'] for r in positive_reviews_with_topic[-10:]]
        if snippets:
            summary_response = llm.invoke(
                topic_summary_prompt_template.format(
                    topic=topic,
                    snippets="\\n".join(snippets))
            )
            topic_summaries[f"positive_{topic}"] = summary_response.content
            time.sleep(2)  # Avoid rate limits
    
    # Process negative topics
    for topic in top_5_negative:
        negative_reviews_with_topic = [
            r for r in final_analysis_list
            if topic in r.get('topics', []) and r.get('sentiment') == "Negative"
        ]
        # Take the last 10 reviews for recency
        snippets = [r['review_text'] for r in negative_reviews_with_topic[-10:]]
        if snippets:
            summary_response = llm.invoke(
                topic_summary_prompt_template.format(
                    topic=topic,
                    snippets="\\n".join(snippets))
            )
            topic_summaries[f"negative_{topic}"] = summary_response.content
            time.sleep(2)  # Avoid rate limits
    
    return {"topic_summaries": topic_summaries}

def generate_final_report_node(state: AgentState):
    """Generates the final summary using the rich context."""
    print("---NODE: GENERATE FINAL REPORT---")
    context = state["summary_context"]
    pos_summary_text = "\n".join([f"- **{topic}:** {summary}" for topic, summary in context['positive_topic_summaries'].items()])
    neg_summary_text = "\n".join([f"- **{topic}:** {summary}" for topic, summary in context['negative_topic_summaries'].items()])
    
    # We add the full analysis list back in for the agent to find trends
    final_prompt = executive_summary_prompt_template.format(
        product_id=context['product_id'],
        positive_percent=f"{context['positive_percent']:.0f}",
        negative_percent=f"{context['negative_percent']:.0f}",
        neutral_percent=f"{context['neutral_percent']:.0f}",
        positive_topic_summaries=pos_summary_text,
        negative_topic_summaries=neg_summary_text,
        analysis_results=json.dumps(state["analysis_results"], default=str)
    )
    print(f"{context['positive_percent']:.0f}, {context['negative_percent']:.0f}, {context['neutral_percent']:.0f}")
    final_summary = llm.invoke(final_prompt)
    return {"summary": final_summary.content}

# --- 3. Build the Graph ---
workflow = StateGraph(AgentState)
workflow.add_node("retrieve_reviews", retrieve_reviews_node)
workflow.add_node("analysis_and_enrichment", analysis_and_enrichment_node)
workflow.add_node("topic_summary", topic_summary_node)
workflow.add_node("generate_final_report", generate_final_report_node)

workflow.set_entry_point("retrieve_reviews")
workflow.add_edge("retrieve_reviews", "analysis_and_enrichment")
workflow.add_edge("analysis_and_enrichment", "topic_summary")
workflow.add_edge("topic_summary", "generate_final_report")
workflow.add_edge("generate_final_report", END)

agent_executor = workflow.compile()
print("✅ Agent graph compiled successfully.")