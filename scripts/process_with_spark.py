import argparse
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Configure professional logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_reviews_from_bq(input_table: str, output_table: str, gcs_temp_bucket: str):
    """
    Reads raw review data from a BigQuery table, cleans it with Spark, 
    and writes the result to another BigQuery table.
    """
    logging.info("Initializing Spark session...")
    spark = SparkSession.builder.appName("Review_Processing_From_BQ").getOrCreate()

    # Configure the BigQuery connector to use a GCS bucket for temporary data storage.
    # This is required for Spark to communicate efficiently with BigQuery.
    spark.conf.set('temporaryGcsBucket', gcs_temp_bucket)

    try:
        logging.info(f"Reading raw data from BigQuery table: {input_table}...")

        # Read directly from a BigQuery table
        raw_df = spark.read.format('bigquery').option('table', input_table).load()
        # ------------------------------

        logging.info("Transforming data...")

        # 1. Select only the columns we need
        # 2. Rename them to be cleaner
        # 3. Filter out rows where the review text is null
        transformed_df = raw_df.select(
            col("Id").alias("review_id"),
            col("ProductId").alias("product_id"),
            col("UserId").alias("user_id"),
            col("Score").alias("rating").cast("integer"),
            col("Time").alias("review_timestamp").cast("timestamp"),
            col("Summary").alias("review_summary"),
            col("Text").alias("review_text")
        ).filter(col("review_text").isNotNull())

        logging.info(f"Writing {transformed_df.count()} cleaned records to BigQuery table {output_table}...")

        # Write the final DataFrame to BigQuery
        transformed_df.write.format('bigquery') \
            .option('table', output_table) \
            .mode('overwrite') \
            .save()

        logging.info("✅ Spark job completed successfully.")

    except Exception as e:
        logging.error(f"An error occurred during the Spark job: {e}")
    finally:
        spark.stop()
        logging.info("Spark session stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_table', required=True, help="Full BigQuery table name for the raw input (e.g., project.dataset.table).")
    parser.add_argument('--output_table', required=True, help="Full BigQuery table name for the clean output (e.g., project.dataset.table).")
    parser.add_argument('--gcs_temp_bucket', required=True, help="GCS bucket for temporary BigQuery connector data.")

    args = parser.parse_args()

    process_reviews_from_bq(
        input_table=args.input_table, 
        output_table=args.output_table,
        gcs_temp_bucket=args.gcs_temp_bucket
    )