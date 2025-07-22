import os
import json
from collections import Counter
from datetime import datetime, timezone
from google.cloud import bigquery
from dotenv import load_dotenv

# --- 1. Setup: Load Environment and CREATE CONFIGURATION INSTANCE ---
print("Worker: Loading environment and configuration...")
load_dotenv(dotenv_path='../../.env') 

from .configuration import AgentConfig
from .graph import retrieve_reviews_node, analysis_and_enrichment_node, topic_summary_node, generate_final_report_node
import time

# Create an INSTANCE of the config and validate it. This is the fix.
try:
    config = AgentConfig(gcp_project_id=os.getenv("GCP_PROJECT_ID"))
    print("✅ Worker: Configuration loaded and validated successfully.")
except ValueError as e:
    raise RuntimeError(f"Worker Configuration Error: {e}")

# Initialize clients using the 'config' instance
BQ_CLIENT = bigquery.Client(project=config.gcp_project_id)
RESULTS_TABLE_ID = f"{config.gcp_project_id}.{config.bigquery_dataset}.analysis_results"

def _save_final_record(record: dict):
    """A simple helper to insert the final, prepared record into BigQuery."""
    errors = BQ_CLIENT.insert_rows_json(RESULTS_TABLE_ID, [record])
    if not errors:
        print(f"WORKER: Successfully saved final record for job {record.get('job_id')} to BigQuery.")
    else:
        print(f"WORKER: Error saving record to BigQuery: {errors}")


def run_full_analysis(job_id: str, product_id: str):
    """
    This is the main function that RQ will execute. This version correctly
    handles the final state object returned by the agent.
    """
    print(f"WORKER: Starting new analysis job {job_id} for product {product_id}")
    
    start_time = datetime.now(timezone.utc)
    status = "running"
    final_results = {}

    try:
        # Initialize the state for the first node
        initial_state = {"product_id": product_id}

        # Fetch all reviews for the product from BigQuery
        retrieval_result = retrieve_reviews_node(initial_state)
        all_reviews = retrieval_result.get('reviews', [])
        total_reviews = len(all_reviews)
        if total_reviews == 0:
            raise ValueError(f"No reviews found for product ID {product_id}.")
        print(f"WORKER: Found {total_reviews} reviews for product {product_id}.")

        # MAP: process reviews in chunks
        chunk_size = 50
        all_enriched_results = []

        for i in range(0, total_reviews, chunk_size):
            chunk_of_reviews = all_reviews[i:i + chunk_size]
            print(f"WORKER: Processing chunk {i // chunk_size + 1} of {-(total_reviews // -chunk_size)} ...")

            # Create a temporary state for this chunk
            chunk_state = {"reviews": chunk_of_reviews, "product_id": product_id}
            # Call the enrichment node directly on the chunk
            enriched_chunk = analysis_and_enrichment_node(chunk_state)
            all_enriched_results.append(enriched_chunk)

            # Avoid hitting rate limits by sleeping between chunks
            time.sleep(10)  # Adjust this sleep time as needed based on your rate limits
            
        # REDUCE: Aggregate the final context and generate the final summary
        print(f"WORKER: Aggregating results from {len(all_enriched_results)} chunks...")
        final_analysis_list = [item for chunk in all_enriched_results for item in chunk['analysis_results']]

        # Calculate Aggregated Statistics
        sentiments = [item.get('sentiment') for item in final_analysis_list]
        total_valid = len(sentiments)
        positive_percent = (sentiments.count("Positive") / total_valid) * 100 if total_valid > 0 else 0
        negative_percent = (sentiments.count("Negative") / total_valid) * 100 if total_valid > 0 else 0
        neutral_percent = (sentiments.count("Neutral") / total_valid) * 100 if total_valid > 0 else 0

        # Calculate Top Topics from ALL reviews
        positive_topics = [
            topic for item in final_analysis_list
            if item.get('sentiment') == "Positive"
            for topic in item.get('topics', [])
        ]
        negative_topics = [
            topic for item in final_analysis_list
            if item.get('sentiment') == "Negative"
            for topic in item.get('topics', [])
        ]
        top_5_positive = [item[0] for item in Counter(positive_topics).most_common(5)]
        top_5_negative = [item[0] for item in Counter(negative_topics).most_common(5)]

        # Prepare the state for the topic summary node
        summary_node_state = {
            "analysis_results": final_analysis_list,
            "top_5_positive_topics": top_5_positive,
            "top_5_negative_topics": top_5_negative,
        }
        summary_result = topic_summary_node(summary_node_state)
        topic_summaries = summary_result["topic_summaries"]
        
        clean_analysis_without_text = []
        for item in final_analysis_list:
            # Copy all key-value pairs except for 'review_text'
            analysis_only = {k: v for k, v in item.items() if k != 'review_text'}
            clean_analysis_without_text.append(analysis_only)

        # Construct the final summary context for the report node
        final_summary_context = {
            "product_id": product_id,
            "positive_percent": positive_percent,
            "negative_percent": negative_percent,
            "neutral_percent": neutral_percent,
            "positive_topic_summaries": {topic: topic_summaries.get(f"positive_{topic}", "") for topic in top_5_positive},
            "negative_topic_summaries": {topic: topic_summaries.get(f"negative_{topic}", "") for topic in top_5_negative},
        }

        # Construct the statistics for the frontend
        statistics = {
            "product_id": product_id,
            "positive_percent": positive_percent,
            "negative_percent": negative_percent,
            "neutral_percent": neutral_percent,
            "top_5_positive_topics": top_5_positive,
            "top_5_negative_topics": top_5_negative,
        }

        # Prepare the final state for the report generation node
        final_report_state = {
            "summary_context": final_summary_context,
            "analysis_results": clean_analysis_without_text,
        }

        final_report = generate_final_report_node(final_report_state)
        if final_report:
            final_results = {
                "summary": final_report.get("summary", ""),
                "details": statistics,
            }
            status = "completed"

    except Exception as e:
        print(f"WORKER: ❌ Job {job_id} failed: {e}")
        status = "failed"
        final_results = {"error": str(e)}
    
    finally:
        # This 'finally' block now correctly receives the full results dictionary
        completed_time = datetime.now(timezone.utc)
        
        final_record = {
            "job_id": job_id,
            "product_id": product_id,
            "status": status,
            "summary": final_results.get("summary"),
            "full_analysis_json": json.dumps(final_results.get("details"), default=str),
            "submitted_at": start_time.isoformat(),
            "completed_at": completed_time.isoformat()
        }
        
        _save_final_record(final_record)