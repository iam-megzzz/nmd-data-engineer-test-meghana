import sys
import json
import os
import pandas as pd
import boto3
from datetime import datetime
from io import StringIO

import orders_analytics

"""
Modify this lambda function to perform the following questions

1. Find the most profitable Region, and its profit
2. What shipping method is most common for each Category
3. Output a glue table containing the number of orders for each Category and Sub Category
"""


def get_s3_path_from_event(event: dict) -> str:
    """
    Returns the S3 object key from the lambda event record
    Returns: object_key
    """
    try:
        # Extract S3 object key from the event
        s3_event = event['Records'][0]['s3']
        object_key = s3_event['object']['key']
        return object_key
    except (KeyError, IndexError) as e:
        raise ValueError(f"Invalid S3 event structure: {e}")


def read_csv_from_s3(s3_client, bucket_name: str, object_key: str) -> pd.DataFrame:
    """
    Read CSV file from S3 and return as pandas DataFrame
    """
    try:
        # Get the object from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        
        # Read CSV content
        csv_content = response['Body'].read().decode('utf-8')
        
        # Parse CSV into DataFrame
        df = pd.read_csv(StringIO(csv_content))
        
        print(f"Successfully read CSV file: {object_key}")
        print(f"DataFrame shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        return df
    
    except Exception as e:
        raise Exception(f"Error reading CSV from S3: {e}")


def write_csv_to_s3(s3_client, df: pd.DataFrame, bucket_name: str, object_key: str) -> None:
    """
    Write DataFrame to S3 as CSV file
    """
    try:
        # Convert DataFrame to CSV string
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=csv_content.encode('utf-8'),
            ContentType='text/csv'
        )
        
        print(f"Successfully wrote CSV file to S3: {object_key}")
    
    except Exception as e:
        raise Exception(f"Error writing CSV to S3: {e}")


def generate_timestamp() -> str:
    """
    Generate timestamp for file naming
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def lambda_handler(event, context):
    """
    Lambda function to process S3 events and perform analytics on orders data
    """
    try:
        print(f"Lambda function triggered with event: {json.dumps(event, indent=2)}")
        
        # Get environment variables
        input_bucket = os.environ.get('INPUT_BUCKET')
        output_bucket = os.environ.get('OUTPUT_BUCKET')
        
        if not input_bucket or not output_bucket:
            raise ValueError("Missing required environment variables: INPUT_BUCKET or OUTPUT_BUCKET")
        
        print(f"Input bucket: {input_bucket}")
        print(f"Output bucket: {output_bucket}")
        
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Get S3 object key from the event (bucket name comes from environment)
        object_key = get_s3_path_from_event(event)
        
        # Verify it's a CSV file
        if not object_key.lower().endswith('.csv'):
            print(f"File {object_key} is not a CSV file, skipping processing")
            return {
                'statusCode': 200,
                'body': json.dumps(f'File {object_key} is not a CSV file, skipping processing')
            }
        
        print(f"Processing CSV file: {object_key}")
        
        # Read CSV file from S3 using environment variable bucket name
        orders_df = read_csv_from_s3(s3_client, input_bucket, object_key)
        
        # Generate analytics reports
        print("Generating analytics reports...")

        reports = orders_analytics.generate_analytics_reports(orders_df)
        
        # Generate timestamp for file naming
        timestamp = generate_timestamp()
        base_filename = os.path.splitext(os.path.basename(object_key))[0]
        
        # Write each report to S3
        uploaded_files = []
        
        # 1. Most profitable region report
        region_report = reports['most_profitable_region']
        region_filename = f"analytics/{base_filename}_most_profitable_region_{timestamp}.csv"
        write_csv_to_s3(s3_client, region_report, output_bucket, region_filename)
        uploaded_files.append(region_filename)
        
        # 2. Most common shipping method for each category
        ship_method_report = reports['most_common_ship_method']
        ship_method_filename = f"analytics/{base_filename}_most_common_ship_method_{timestamp}.csv"
        write_csv_to_s3(s3_client, ship_method_report, output_bucket, ship_method_filename)
        uploaded_files.append(ship_method_filename)
        
        # 3. Number of orders by category and sub-category
        category_report = reports['orders_by_category']
        category_filename = f"analytics/{base_filename}_orders_by_category_{timestamp}.csv"
        write_csv_to_s3(s3_client, category_report, output_bucket, category_filename)
        uploaded_files.append(category_filename)
        
        # 4. Orders with profit calculations (bonus report)
        orders_with_profit = reports['orders_with_profit']
        profit_filename = f"analytics/{base_filename}_orders_with_profit_{timestamp}.csv"
        write_csv_to_s3(s3_client, orders_with_profit, output_bucket, profit_filename)
        uploaded_files.append(profit_filename)
        
        # Create a summary report
        summary_data = {
            'Processing_Time': timestamp,
            'Input_File': object_key,
            'Records_Processed': len(orders_df),
            'Reports_Generated': len(uploaded_files),
            'Output_Files': uploaded_files
        }
        
        summary_df = pd.DataFrame([summary_data])
        summary_filename = f"analytics/{base_filename}_processing_summary_{timestamp}.csv"
        write_csv_to_s3(s3_client, summary_df, output_bucket, summary_filename)
        
        print(f"Successfully processed {len(orders_df)} records")
        print(f"Generated {len(uploaded_files)} analytics reports")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Analytics processing completed successfully',
                'input_file': object_key,
                'records_processed': len(orders_df),
                'reports_generated': uploaded_files,
                'summary_file': summary_filename
            })
        }
    
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Analytics processing failed'
            })
        }

