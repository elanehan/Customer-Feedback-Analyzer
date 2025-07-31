import os
import sys
from redis import from_url
from rq import Queue
from rq.worker import SimpleWorker
from dotenv import load_dotenv

# Add the project's root directory to the Python path
sys.path.insert(0, os.getcwd()) 

# Load the .env file from the backend directory
load_dotenv(dotenv_path='backend/.env')

# --- Configuration ---
listen = ['default']
redis_url = os.getenv('REDIS_URI', 'redis://localhost:6379')
conn = from_url(redis_url)

if __name__ == '__main__':
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