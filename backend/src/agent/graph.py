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
from typing import List

from langchain_core.prompts import PromptTemplate
from agent.state import AgentState
from agent.tools_and_schemas import get_reviews_from_bigquery
from agent.prompts import batch_analysis_prompt_template, summary_prompt_template
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
# This is the robust pattern we discussed.
llm = ChatGoogleGenerativeAI(model=config.gemini_model_name, google_api_key=gemini_api_key, temperature=0, max_retries=2)
# sentiment_llm = llm.with_structured_output(SentimentAnalysis)
# topics_llm = llm.with_structured_output(TopicExtraction)

# --- 4. Define the Node Functions ---
# The logic inside these nodes remains the same. They will use the llm clients defined above.

def retrieve_reviews_node(state: AgentState):
    """Fetches reviews from BigQuery using the product_id from the state."""
    print("---NODE: RETRIEVE REVIEWS---")
    product_id = state["product_id"]
    reviews = get_reviews_from_bigquery.invoke({"product_id": product_id})
    return {"reviews": reviews}

# def analyze_sentiment_node(state: AgentState):
#     """Analyzes sentiment for each review. Runs in parallel with topic extraction."""
#     print("---NODE: ANALYZE SENTIMENT---")
#     reviews = state["reviews"]
#     sentiments = []
#     for review in reviews:
#         review_text = review.get("review_text", "")
#         # The .invoke method on the structured LLM will return a Pydantic object directly
#         # It's robust to parsing errors by default.
#         response = sentiment_llm.invoke(sentiment_prompt_template.format(review_text=review_text))
#         sentiments.append(response)
#     return {"sentiment_outputs": sentiments}

# def extract_topics_node(state: AgentState):
#     """Extracts topics from each review. Runs in parallel with sentiment analysis."""
#     print("---NODE: EXTRACT TOPICS---")
#     reviews = state["reviews"]
#     topics = []
#     for review in reviews:
#         response = topics_llm.invoke(topic_prompt_template.format(review_text=review.get("review_text", "")))
#         topics.append(response)
#     return {"topic_outputs": topics}

def batch_analysis_node(state: AgentState):
    """
    Analyzes all reviews in a single, efficient batch call to the LLM.
    This replaces the previous looping approach.
    """
    print("---NODE: BATCH ANALYSIS---")
    reviews = state["reviews"]
    
    # 1. Prepare the input for the LLM
    reviews_for_analysis = [
        {
            "review_text": r.get("review_text", ""),
            "review_timestamp": r.get("review_timestamp")
        }
        for r in reviews
    ]
    # We now use our safe JSON serializer to handle the datetime objects correctly
    review_list_json = json.dumps(reviews_for_analysis, default=json_serial)
    
    # 2. Create the prompt and the chain
    # We use the main llm here, as we'll parse the complex JSON response ourselves.
    analysis_chain = batch_analysis_prompt_template | llm 

    # 3. Make ONE powerful API call instead of 100+
    print(f"Analyzing {len(reviews)} reviews in a single batch call...")
    response = analysis_chain.invoke({"review_list_json": review_list_json})
    print("--- Batch analysis complete. Parsing and combining results... ---")
    
    # 4. Parse the response and combine it with the original data
    try:
        # Use our safe parser from utils.py in case the LLM response isn't perfect
        parsed_response = parse_llm_json_output(response.content)
        llm_analyses = parsed_response.get("analyses", [])

        combined_results = []
        # Loop through the ORIGINAL reviews and merge with the analysis results
        for i, review in enumerate(reviews):
            # Fallback in case the LLM didn't return an analysis for every review
            analysis_data = llm_analyses[i] if i < len(llm_analyses) else {"sentiment": "Error", "topics": []}
            
            timestamp_str = review.get("review_timestamp").isoformat() if review.get("review_timestamp") else None
            
            combined_results.append({
                "review": review.get("review_text"),
                "rating": review.get("rating"),
                "sentiment": analysis_data.get("sentiment"),
                "topics": analysis_data.get("topics", []),
                "review_timestamp": timestamp_str
            })
            
        return {"analysis_results": combined_results}
    
    except Exception as e:
        print(f"Error parsing batch analysis response: {e}")
        # If parsing fails, we can add an error state or empty results
        return {"analysis_results": []}
    
# def aggregate_results_node(state: AgentState):
#     """A 'joiner' node that combines the parallel analysis outputs into a single structure."""
#     print("---NODE: AGGREGATE RESULTS---")
#     reviews = state["reviews"]
#     sentiment_outputs = state["sentiment_outputs"]
#     topic_outputs = state["topic_outputs"]
    
#     combined_results = []
#     for i, review in enumerate(reviews):
#         timestamp_str = review.get("review_timestamp").isoformat() if review.get("review_timestamp") else None
#         combined_results.append({
#             "review": review.get("review_text"),
#             "rating": review.get("rating"),
#             "sentiment": sentiment_outputs[i].sentiment,
#             "topics": topic_outputs[i].topics,
#             "review_timestamp": timestamp_str
#         })
        
#     return {"analysis_results": combined_results}

def generate_summary_node(state: AgentState):
    """The final node. Takes all structured analysis and generates a human-readable summary."""
    print("---NODE: GENERATE SUMMARY---")
    analysis_results_str = json.dumps(state["analysis_results"], indent=2)
    
    summary_response = llm.invoke(summary_prompt_template.format(analysis_results=analysis_results_str))
    return {
        "summary": summary_response.content,
        "analysis_results": state["analysis_results"] 
    }


# --- 5. Build the Graph ---
# This section remains the same.

workflow = StateGraph(AgentState)

workflow.add_node("retrieve_reviews", retrieve_reviews_node)
# workflow.add_node("analyze_sentiment", analyze_sentiment_node)
# workflow.add_node("extract_topics", extract_topics_node)
# workflow.add_node("aggregate_results", aggregate_results_node)
workflow.add_node("batch_analysis", batch_analysis_node)
workflow.add_node("generate_summary", generate_summary_node)

workflow.set_entry_point("retrieve_reviews")
# workflow.add_edge("retrieve_reviews", "analyze_sentiment")
# workflow.add_edge("retrieve_reviews", "extract_topics")
# workflow.add_edge(["analyze_sentiment", "extract_topics"], "aggregate_results")
# workflow.add_edge("aggregate_results", "generate_summary")
workflow.add_edge("retrieve_reviews", "batch_analysis")
workflow.add_edge("batch_analysis", "generate_summary")
workflow.add_edge("generate_summary", END)

agent_executor = workflow.compile()
print("Agent graph compiled successfully.")