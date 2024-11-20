#!/usr/bin/env python3

import os
import sys
import logging
import subprocess
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ParamValidationError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def validate_s3_bucket(bucket_name):
    """
    Validate S3 bucket existence and accessibility
    
    Args:
        bucket_name (str): Name of the S3 bucket
    
    Returns:
        bool: True if bucket is valid and accessible, False otherwise
    """
    try:
        s3_client = boto3.client('s3')
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '403':
            logger.error(f"Access denied to bucket: {bucket_name}")
        elif error_code == '404':
            logger.error(f"Bucket not found: {bucket_name}")
        else:
            logger.error(f"Unexpected error validating bucket: {e}")
        return False
    except (NoCredentialsError, ParamValidationError) as e:
        logger.error(f"Credentials or parameter error: {e}")
        return False

def find_latest_backup(bucket_name, prefix):
    """
    Find the latest backup file in S3
    
    Args:
        bucket_name (str): S3 bucket name
        prefix (str): S3 key prefix for backup files
    
    Returns:
        str or None: Latest backup file key, or None if no backups found
    """
    try:
        s3_client = boto3.client('s3')
        response = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        backups = [obj['Key'] for obj in response.get('Contents', []) 
                   if obj['Key'].endswith('.tar.gz')]
        
        if not backups:
            logger.warning(f"No backups found in {bucket_name}/{prefix}")
            return None
        
        return max(backups, key=lambda x: x.split('_')[-1])
    
    except ClientError as e:
        logger.error(f"Error listing S3 objects: {e}")
        return None

def download_backup(bucket_name, backup_key, local_path):
    """
    Download backup from S3
    
    Args:
        bucket_name (str): S3 bucket name
        backup_key (str): S3 object key for backup
        local_path (str): Local path to save backup
    
    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        s3_client = boto3.client('s3')
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        s3_client.download_file(
            Bucket=bucket_name, 
            Key=backup_key, 
            Filename=local_path
        )
        
        logger.info(f"Backup downloaded: {local_path}")
        return True
    
    except ClientError as e:
        logger.error(f"S3 download error: {e}")
        return False

def prepare_postgres_directory(postgres_data_dir):
    """
    Prepare PostgreSQL data directory for future Docker deployment
    
    Args:
        postgres_data_dir (str): Path to PostgreSQL data directory
    
    Returns:
        bool: True if directory preparation successful, False otherwise
    """
    try:
        # Ensure directory exists with correct permissions
        os.makedirs(postgres_data_dir, exist_ok=True)
        
        # Set permissions to match PostgreSQL container expectations
        subprocess.run(['chmod', '700', postgres_data_dir], check=True)
        
        logger.info(f"PostgreSQL data directory prepared: {postgres_data_dir}")
        return True
    
    except (OSError, subprocess.CalledProcessError) as e:
        logger.error(f"Error preparing PostgreSQL directory: {e}")
        return False

def extract_backup(backup_path, postgres_data_dir):
    """
    Extract backup to PostgreSQL data directory
    
    Args:
        backup_path (str): Path to backup tar.gz file
        postgres_data_dir (str): Path to PostgreSQL data directory
    
    Returns:
        bool: True if extraction successful, False otherwise
    """
    try:
        # Extract backup preserving permissions
        subprocess.run([
            'tar', 
            '-xzpf', 
            backup_path, 
            '-C', 
            postgres_data_dir
        ], check=True)
        
        logger.info(f"Backup extracted to {postgres_data_dir}")
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Backup extraction error: {e}")
        return False

def stage_database_backup(
    s3_bucket='amta-app', 
    s3_prefix='amta-db',
    backup_dir='/tmp/database_backups',
    postgres_data_dir = os.getenv('POSTGRES_DATA_DIR', '/var/lib/postgresql/data')

):
    """
    Stage database backup from S3
    
    Args:
        s3_bucket (str): S3 bucket name
        s3_prefix (str): S3 key prefix for backups
        backup_dir (str): Local directory for temporary backup storage
        postgres_data_dir (str): PostgreSQL data directory
    
    Returns:
        bool: True if entire staging process successful, False otherwise
    """
    # Validate S3 bucket
    if not validate_s3_bucket(s3_bucket):
        return False
    
    # Find latest backup
    latest_backup_key = find_latest_backup(s3_bucket, s3_prefix)
    if not latest_backup_key:
        return False
    
    # Prepare local backup path
    local_backup_path = os.path.join(backup_dir, os.path.basename(latest_backup_key))
    
    # Download backup
    if not download_backup(s3_bucket, latest_backup_key, local_backup_path):
        return False
    
    # Prepare PostgreSQL directory
    if not prepare_postgres_directory(postgres_data_dir):
        return False
    
    # Extract backup
    if not extract_backup(local_backup_path, postgres_data_dir):
        return False
    
    logger.info("Database backup staging completed successfully")
    return True

def main():
    success = stage_database_backup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
