import os
import json
from datetime import datetime, timezone
from google.cloud import bigquery
from dotenv import load_dotenv

# --- 1. Setup: Load Environment and CREATE CONFIGURATION INSTANCE ---
print("Worker: Loading environment and configuration...")
load_dotenv(dotenv_path='../../.env') 

from .configuration import AgentConfig
from .graph import agent_executor

# Create an INSTANCE of the config and validate it. This is the fix.
try:
    config = AgentConfig(gcp_project_id=os.getenv("GCP_PROJECT_ID"))
    print("✅ Worker: Configuration loaded and validated successfully.")
except ValueError as e:
    raise RuntimeError(f"Worker Configuration Error: {e}")

# Initialize clients using the 'config' instance
BQ_CLIENT = bigquery.Client(project=config.gcp_project_id)
RESULTS_TABLE_ID = f"{config.gcp_project_id}.{config.bigquery_dataset}.analysis_results"


def _save_job_status(job_id: str, product_id: str, status: str, result_data: dict = None):
    # This helper function has been updated to use the full RESULTS_TABLE_ID
    # and BQ_CLIENT which are now correctly initialized.
    
    # We create the submission and completion timestamps inside the main function now.
    # This helper will just save what it's given.
    
    rows_to_insert = [{
        "job_id": job_id,
        "product_id": product_id,
        "status": status,
        "summary": result_data.get("summary") if result_data else None,
        "full_analysis_json": json.dumps(result_data, default=str) if result_data else None,
        "submitted_at": result_data.get("submitted_at"),
        "completed_at": result_data.get("completed_at")
    }]
    
    errors = BQ_CLIENT.insert_rows_json(RESULTS_TABLE_ID, rows_to_insert)
    if not errors:
        print(f"WORKER: Successfully saved status '{status}' for job {job_id} to BigQuery.")
    else:
        print(f"WORKER: Error saving job {job_id} to BigQuery: {errors}")


def run_full_analysis(job_id: str, product_id: str):
    """
    This is the main function that RQ will execute in the background.
    It uses .stream() for robust execution and saves the final result.
    """
    print(f"WORKER: Starting new analysis job {job_id} for product {product_id}")
    
    start_time = datetime.now(timezone.utc)
    status = "running"
    final_results = {}
    
    # We still have the main try/except block to catch catastrophic failures
    try:
        initial_state = {"product_id": product_id}
        final_state_chunk = None
        
        # We will use .stream() to execute the graph.
        # This is more robust as it gives us the state after the last successful node, even on failure.
        for chunk in agent_executor.stream(initial_state, {"recursion_limit": 10}):
            # We don't print every step, we just save the latest state
            final_state_chunk = chunk

        # After the loop finishes, check the final state
        if final_state_chunk and "generate_summary" in final_state_chunk:
            final_results = final_state_chunk['generate_summary']
            status = "complete"
            print(f"WORKER: ✅ Finished job {job_id}")
        else:
            # If the loop finished but the final node isn't 'generate_summary', something went wrong.
            last_node = list(final_state_chunk.keys())[0] if final_state_chunk else "N/A"
            raise ValueError(f"Agent did not produce a final summary. Last successful node was: '{last_node}'.")

    except Exception as e:
        print(f"WORKER: ❌ Job {job_id} failed: {e}")
        status = "failed"
        final_results = {"error": str(e)}
    
    finally:
        # --- Save one final record to BigQuery ---
        completed_time = datetime.now(timezone.utc)
        
        record_to_save = {
            "summary": final_results.get("summary"),
            # The 'full_analysis_json' field now accurately stores the final agent state or the error
            "full_analysis_json": final_results, 
            "submitted_at": start_time.isoformat(),
            "completed_at": completed_time.isoformat()
        }
        
        # The helper function remains the same
        _save_job_status(job_id, product_id, status, record_to_save)