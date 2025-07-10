import os
import json
from datetime import datetime, timezone
from google.cloud import bigquery
from dotenv import load_dotenv

# --- 1. Setup: Load Environment and CREATE CONFIGURATION INSTANCE ---
print("Worker: Loading environment and configuration...")
load_dotenv(dotenv_path='../../.env') 

from .configuration import AgentConfig
from .graph import agent_executor, batch_analysis_node, generate_summary_node
from .tools_and_schemas import get_reviews_from_bigquery

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
        # Fetch all reviews for the product from BigQuery
        all_reviews = get_reviews_from_bigquery.invoke(product_id)
        total_reviews = len(all_reviews)
        if total_reviews == 0:
            raise ValueError(f"No reviews found for product ID {product_id}.")
        print(f"WORKER: Found {total_reviews} reviews for product {product_id}.")

        # MAP: process reviews in chunks
        chunk_size = 50
        all_analysis_results = []

        for i in range(0, total_reviews, chunk_size):
            chunk_of_reviews = all_reviews[i:i + chunk_size]
            print(f"WORKER: Processing chunk {i // chunk_size + 1} of {-(total_reviews // -chunk_size)} ...")

            # Create a temporary state for this chunk
            chunk_state = {"reviews": chunk_of_reviews}
            # Run just the batch analysis node on this chunk
            chunk_results = batch_analysis_node(chunk_state)
            all_analysis_results.extend(chunk_results.get("analysis_results", []))

        # Reduce: generate a summary from all analysis results
        print(f"WORKER: Generating summary for {len(all_analysis_results)} analysis results...")
        summary_state = {"analysis_results": all_analysis_results}
        summary_output = generate_summary_node(summary_state)
        final_results = {
            "summary": summary_output.get("summary"),
            "analysis_results": all_analysis_results
        }
        status = "completed"
        print(f"WORKER: ✅ Job {job_id} finished successfully.")

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
            "full_analysis_json": json.dumps(final_results.get("analysis_results"), default=str),
            "submitted_at": start_time.isoformat(),
            "completed_at": completed_time.isoformat()
        }
        
        _save_final_record(final_record)