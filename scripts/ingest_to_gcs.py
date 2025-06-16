# scripts/ingest_to_gcs.py

import argparse
import logging
import os
from google.cloud import storage

# Configure professional logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def upload_to_gcs(project_id: str, bucket_name: str, source_file_path: str, destination_blob_name: str):
    """
    Uploads a local file to a Google Cloud Storage bucket.

    Args:
        project_id (str): Your Google Cloud project ID.
        bucket_name (str): The name of your GCS bucket.
        source_file_path (str): The local path to the file to upload.
        destination_blob_name (str): The desired path (blob name) in the GCS bucket.
    """
    if not os.path.exists(source_file_path):
        logging.error(f"Error: The source file {source_file_path} was not found.")
        return

    try:
        logging.info(f"Attempting to upload '{source_file_path}' to 'gs://{bucket_name}/{destination_blob_name}'...")
        
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_path)

        logging.info("✅ Upload successful.")

    except Exception as e:
        logging.error(f"An error occurred during upload: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload a file to Google Cloud Storage.")
    
    parser.add_argument("--project", required=True, help="Your Google Cloud project ID.")
    parser.add_argument("--bucket", required=True, help="The destination GCS bucket name.")
    parser.add_argument("--source", required=True, help="The local source file path.")
    parser.add_argument("--destination", default="raw_data/amazon_reviews.csv", help="The destination blob name in the GCS bucket.")

    args = parser.parse_args()

    upload_to_gcs(
        project_id=args.project,
        bucket_name=args.bucket,
        source_file_path=args.source,
        destination_blob_name=args.destination
    )

# Example usage for docker:
# docker run -e GOOGLE_APPLICATION_CREDENTIALS="/app/keyfile.json" \
#        -v /path/on/your/mac/keyfile.json:/app/keyfile.json \
#        your-ingestion-image \
#        --project="your-gcp-project-id" \
#        --bucket="your-unique-bucket-name" \
#        --source="/app/data/Reviews.csv" \
#        --destination="raw_data/amazon_reviews.csv"