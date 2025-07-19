# # mypy: disable - error - code = "no-untyped-def,misc"
# import pathlib
# from fastapi import FastAPI, Response
# from fastapi.staticfiles import StaticFiles

# # Define the FastAPI app
# app = FastAPI()


# def create_frontend_router(build_dir="../frontend/dist"):
#     """Creates a router to serve the React frontend.

#     Args:
#         build_dir: Path to the React build directory relative to this file.

#     Returns:
#         A Starlette application serving the frontend.
#     """
#     build_path = pathlib.Path(__file__).parent.parent.parent / build_dir

#     if not build_path.is_dir() or not (build_path / "index.html").is_file():
#         print(
#             f"WARN: Frontend build directory not found or incomplete at {build_path}. Serving frontend will likely fail."
#         )
#         # Return a dummy router if build isn't ready
#         from starlette.routing import Route

#         async def dummy_frontend(request):
#             return Response(
#                 "Frontend not built. Run 'npm run build' in the frontend directory.",
#                 media_type="text/plain",
#                 status_code=503,
#             )

#         return Route("/{path:path}", endpoint=dummy_frontend)

#     return StaticFiles(directory=build_path, html=True)


# # Mount the frontend under /app to not conflict with the LangGraph API routes
# app.mount(
#     "/app",
#     create_frontend_router(),
#     name="frontend",
# )

# backend/src/agent/app.py

import os
import json
import uuid
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from redis import Redis
from rq import Queue
from rq.job import Job
from google.cloud import bigquery
from dotenv import load_dotenv
import time

# --- 1. Setup ---
print("API Server: Loading environment and configuration...")
load_dotenv(dotenv_path='../../.env')

from .configuration import AgentConfig

try:
    config = AgentConfig(gcp_project_id=os.getenv("GCP_PROJECT_ID"))
    print("✅ API Server: Configuration loaded and validated successfully.")
except ValueError as e:
    raise RuntimeError(f"API Server Configuration Error: {e}")

# --- 2. Initialize Clients ---
print("API Server: Connecting to Redis and BigQuery...")
redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
q = Queue(name="default", connection=redis_conn)

BQ_CLIENT = bigquery.Client(project=config.gcp_project_id)
RESULTS_TABLE_ID = f"{config.gcp_project_id}.{config.bigquery_dataset}.analysis_results"

# --- 3. Define API Models ---
class AnalyzeRequest(BaseModel):
    product_id: str

class AnalyzeResponse(BaseModel):
    message: str
    job_id: str

app = FastAPI()

# --- 4. Define API Endpoints ---

@app.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_analysis(request: AnalyzeRequest):
    """
    This endpoint now uses the robust two-step method to create and enqueue a job.
    """
    product_id = request.product_id
    job_id = str(uuid.uuid4()) # Our custom ID that we want to use

    print(f"API Server: Creating job with custom ID: {job_id}")

    # --- THE NEW, ROBUST METHOD ---

    # Step 1: Create the Job object manually.
    # This gives us full control and avoids any argument name collisions.
    job = Job.create(
        func='backend.src.agent.worker.run_full_analysis', # The function to run
        args=(job_id, product_id),                          # The arguments, as a tuple in the correct order
        connection=redis_conn,
        id=job_id,                                          # Explicitly set the Job's ID
        result_ttl=86400,                                   # Keep success records for 1 day
        failure_ttl=604800,                                 # Keep failed records for 7 days
        timeout='1h'                                        # Set a 1-hour timeout for the job
    )

    # Step 2: Enqueue the pre-made Job object onto the 'default' queue.
    q.enqueue_job(job)
    
    print(f"--- API: Successfully enqueued job {job.id}. ---")

    # The job ID returned to the user now correctly matches the one in the queue.
    return {"message": "Analysis started", "job_id": job.id}



@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Check the live job status by its ID from RQ
    and retrieve results from BigQuery if completed.
    """
    print(f"API Server: Checking status for job ID: {job_id}")
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job ID {job_id} not found: {e}")
    
    job_status = job.get_status()

    # If the job is finished, fetch results from BigQuery
    if job_status == 'finished':
        print(f"API Server: Job {job_id} finished. Fetching results from BigQuery...")
        try:
            query = f"SELECT status, summary, full_analysis_json FROM `{RESULTS_TABLE_ID}` WHERE job_id = '{job_id}' LIMIT 1"
            query_job = BQ_CLIENT.query(query)
            results = list(query_job)

            if results:
                job_data = dict(results[0])
                # The final status should be 'completed' or 'failed' based on the worker's logic
                final_status = job_data.get('status', 'unknown')

                details = json.loads(job_data.get('full_analysis_json', '{}')) if job_data.get('full_analysis_json') else {}

                return {"job_id": job_id, "status": final_status, "result": {"summary": job_data.get('summary'), "details": details}}
            else:
                # If the RQ job is finished but the worker hasn't finished saving results yet
                return {"job_id": job_id, "status": "saving_results"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching results from BigQuery: {str(e)}")
        
    # If the job failed, we can get the error info from RQ
    elif job_status == 'failed':
        return {"job_id": job_id, "status": "failed", "result": {"error": str(job.exc_info)}}
    
    # Otherwise, the job is still running or queued
    else:
        return {"job_id": job_id, "status": job_status, "result": None}