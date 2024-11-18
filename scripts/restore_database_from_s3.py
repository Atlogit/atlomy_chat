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
    Create S3 client with fallback to instance credentials
    Prioritizes explicit credentials, then falls back to instance role
    """
    try:
        # Try explicit credentials first
        session = boto3.Session(
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.environ.get('AWS_SESSION_TOKEN')
        )
        return session.client('s3')
    except Exception as explicit_error:
        logger.warning(f"Explicit credentials failed: {explicit_error}")
        
        try:
            # Fallback to default credentials (EC2 instance role)
            return boto3.client('s3')
        except Exception as default_error:
            logger.error(f"S3 client creation failed: {default_error}")
            return None

def stage_database_backup(
    s3_bucket=None, 
    s3_prefix='amta-db',
    backup_dir='database_backups'
):
    """
    Stage database backup from S3 without attempting restoration
    Prepares backup for future use during Docker deployment
    """
    # Hardcode the bucket name based on toolkit scripts
    s3_bucket = 'amta-app'
    deployment_mode = os.environ.get('DEPLOYMENT_MODE', 'production')

    logger.info(f"Starting database backup staging process")
    logger.info(f"Deployment Mode: {deployment_mode}")
    logger.info(f"S3 Bucket: {s3_bucket}")
    logger.info(f"S3 Prefix: {s3_prefix}")

    # Log GitHub Actions role information
    logger.info("GitHub Actions Role Details:")
    logger.info(f"Role ARN: {os.environ.get('GITHUB_ACTIONS_ROLE_ARN', 'Not Set')}")

    try:
        # Create S3 client with fallback mechanism
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
        except NoCredentialsError:
            logger.error("No AWS credentials found. Ensure proper IAM role is attached.")
            logger.error("Recommended Actions:")
            logger.error("1. Verify GitHub Actions workflow has correct AWS credentials")
            logger.error("2. Check IAM role permissions for s3:ListBucket")
            return False
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(f"S3 ListObjects error: {error_code}")
            logger.error(f"Detailed Error: {error_message}")
            
            if error_code == 'AccessDenied':
                logger.error("Access Denied Troubleshooting:")
                logger.error("1. Update GitHub Actions IAM role to include s3:ListBucket permission")
                logger.error("2. Verify the role has access to 'amta-app' S3 bucket")
                logger.error("3. Check AWS account and bucket policies")
            
            return False
        except BotoCoreError as e:
            logger.error(f"Boto3 core error during S3 interaction: {e}")
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
        try:
            s3_client.download_file(
                s3_bucket, 
                latest_backup, 
                local_backup_path
            )
        except Exception as download_error:
            logger.error(f"Failed to download backup: {download_error}")
            return False
        
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
