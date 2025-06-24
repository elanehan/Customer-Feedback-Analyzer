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
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = from_url(redis_url)

if __name__ == '__main__':
    # We now create an instance of the specific SimpleWorker class.
    # We no longer pass the worker_class argument.
    queues = [Queue(name, connection=conn) for name in listen]
    worker = SimpleWorker(
        queues=queues,  # List of Queue instances
        connection=conn           # The Redis connection object
    )
    
    print("--- Starting RQ SimpleWorker ---")
    
    # The work() method starts the worker's listening loop
    worker.work(with_scheduler=False)