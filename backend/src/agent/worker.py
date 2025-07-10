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
        initial_state = {"product_id": product_id}
        
        print("--- WORKER: Invoking agent executor... ---")
        final_state = agent_executor.invoke(initial_state, {"recursion_limit": 10})
        print("--- WORKER: Agent execution complete. ---")

        # --- THIS IS THE CORRECTED LOGIC ---
        # We now check for the 'summary' key directly in the final_state object.
        if final_state and final_state.get("summary"):
            
            # The 'final_state' IS the dictionary of results we want.
            final_results = final_state 
            status = "complete"
            print(f"WORKER: ✅ Job {job_id} finished successfully.")
            
        else:
            raise ValueError(f"Agent finished but did not produce a summary. Final state keys: {list(final_state.keys())}")

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