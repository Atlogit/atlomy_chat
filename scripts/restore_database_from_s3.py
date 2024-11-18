#!/usr/bin/env python3

import os
import sys
import logging
import socket
import boto3
import psycopg2
import subprocess
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_s3_client():
    """
    Create S3 client with GitHub Actions credentials
    """
    try:
        return boto3.client('s3')
    except Exception as error:
        logger.error(f"S3 client creation failed: {error}")
        return None

def stage_database_backup(
    s3_bucket='amta-app', 
    s3_prefix='amta-db',
    backup_dir='database_backups'
):
    """
    Stage database backup from S3 without attempting restoration
    Prepares backup for future use during Docker deployment
    """
    deployment_mode = os.environ.get('DEPLOYMENT_MODE', 'production')

    logger.info(f"Starting database backup staging process")
    logger.info(f"Deployment Mode: {deployment_mode}")
    logger.info(f"S3 Bucket: {s3_bucket}")
    logger.info(f"S3 Prefix: {s3_prefix}")

    try:
        # Create S3 client
        s3_client = create_s3_client()
        if not s3_client:
            logger.error("Failed to create S3 client")
            return False
        
        # List objects in S3 bucket
        try:
            response = s3_client.list_objects_v2(
                Bucket=s3_bucket,
                Prefix=s3_prefix
            )
        except ClientError as e:
            logger.error(f"S3 ListObjects error: {e}")
            return False
        
        # Find the latest backup file
        backups = [obj['Key'] for obj in response.get('Contents', []) 
                   if obj['Key'].endswith('.tar.gz') or obj['Key'].endswith('.sql.gz')]
        
        if not backups:
            logger.warning("No database backups found in S3.")
            return False
        
        latest_backup = max(backups, key=lambda x: x.split('_')[-1])
        
        # Create local backup directory
        os.makedirs(backup_dir, exist_ok=True)
        local_backup_path = os.path.join(backup_dir, os.path.basename(latest_backup))
        
        # Download backup
        s3_client.download_file(
            s3_bucket, 
            latest_backup, 
            local_backup_path
        )
        
        logger.info(f"Database backup staged successfully: {local_backup_path}")
        return True
    
    except Exception as e:
        logger.error(f"Unexpected error during database backup staging: {e}")
        return False

def main():
    """
    Main entry point for script
    Allows direct execution with optional configuration
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Stage database backup from S3')
    parser.add_argument('--s3-prefix', help='S3 prefix/folder', default='amta-db')
    parser.add_argument('--backup-dir', help='Local backup directory', default='database_backups')
    
    args = parser.parse_args()
    
    # Attempt to stage backup
    success = stage_database_backup(
        s3_prefix=args.s3_prefix,
        backup_dir=args.backup_dir
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
