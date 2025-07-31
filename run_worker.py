import os
import sys
import threading
from redis import from_url
from rq import Queue
from rq.worker import SimpleWorker
from dotenv import load_dotenv
from flask import Flask

# Add the project's root directory to the Python path
sys.path.insert(0, os.getcwd()) 

# Load the .env file from the backend directory
load_dotenv(dotenv_path='backend/.env')

# Create Flask app for health checks
app = Flask(__name__)

@app.route('/')
def health_check():
    return {"status": "Worker is running", "message": "RQ Worker is healthy"}, 200

@app.route('/health')
def health():
    return {"status": "healthy"}, 200

def run_worker():
    """Run the RQ worker in a separate thread"""
    # --- Configuration ---
    listen = ['default']
    redis_url = os.getenv('REDIS_URI', 'redis://localhost:6379')
    conn = from_url(redis_url)

    print("--- Starting RQ SimpleWorker ---")
    print(f"Redis URL: {redis_url}")
    print(f"Listening on queues: {listen}")
    
    try:
        # Create Queue instances for each queue name
        queues = [Queue(name, connection=conn) for name in listen]
        
        # Create the worker instance
        worker = SimpleWorker(
            queues=queues,      # List of Queue instances
            connection=conn     # The Redis connection object
        )
        
        print("Worker created successfully. Starting work loop...")
        
        # Start the worker's listening loop
        worker.work(with_scheduler=False)
        
    except KeyboardInterrupt:
        print("\n--- Worker interrupted by user ---")
        sys.exit(0)
    except Exception as e:
        print(f"--- Worker failed to start: {e} ---")
        sys.exit(1)

if __name__ == '__main__':
    # Start the worker in a background thread
    worker_thread = threading.Thread(target=run_worker, daemon=True)
    worker_thread.start()
    
    # Start the Flask app for health checks on the port Cloud Run expects
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting Flask health check server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)