import os
from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from google.cloud import bigquery
from .configuration import AgentConfig

# class SearchQueryList(BaseModel):
#     query: List[str] = Field(
#         description="A list of search queries to be used for web research."
#     )
#     rationale: str = Field(
#         description="A brief explanation of why these queries are relevant to the research topic."
#     )


# class Reflection(BaseModel):
#     is_sufficient: bool = Field(
#         description="Whether the provided summaries are sufficient to answer the user's question."
#     )
#     knowledge_gap: str = Field(
#         description="A description of what information is missing or needs clarification."
#     )
#     follow_up_queries: List[str] = Field(
#         description="A list of follow-up queries to address the knowledge gap."
#     )


# --- 1. Pydantic Schemas for Structured LLM Output ---
# These models define the exact JSON structure we want the LLM to return for each analysis task.
# This makes our agent's output reliable and easy to parse.

# class SentimentAnalysis(BaseModel):
#     """A single sentiment analysis result."""
#     sentiment: Literal["Positive", "Negative", "Neutral"] = Field(
#         description="The sentiment of the review."
#     )

# class TopicExtraction(BaseModel):
#     """A list of extracted topics from a review."""
#     topics: List[str] = Field(
#         description="A list of 1 to 3 key topics or features, such as 'Battery Life' or 'Screen Quality', mentioned in the customer review."
#     )

# --- 2. The BigQuery Tool ---
# This tool allows the agent to interact with our data warehouse.

@tool
def get_reviews_from_bigquery(product_id: str) -> List[dict]:
    """Queries the BigQuery warehouse to get customer reviews for a specific product ID."""
    print(f"--- Calling BigQuery Tool for Product ID: {product_id} ---")
    
    # It's best practice to get configuration from environment variables
    project_id = os.getenv("GCP_PROJECT_ID")
    config = AgentConfig(gcp_project_id=project_id)
    dataset_id = config.bigquery_dataset  # Use the dataset from the config
    table_name = config.bigquery_table  # Use the table name from the config

    if not project_id:
        raise ValueError("GCP_PROJECT_ID environment variable is not set.")

    client = bigquery.Client(project=project_id)
    
    # This query fetches the reviews from the clean table you created
    query = f"""
        SELECT review_text, rating, review_timestamp
        FROM `{project_id}.{dataset_id}.{table_name}`
        WHERE product_id = '{product_id}'
        ORDER BY review_timestamp ASC
    """
    # NOTE: We add a LIMIT for testing to keep costs low and development fast.
    
    try:
        query_job = client.query(query)
        results = [dict(row) for row in query_job]
        print(f"--- Found {len(results)} reviews in BigQuery. ---")
        return results
    except Exception as e:
        print(f"--- Error querying BigQuery: {e} ---")
        return []