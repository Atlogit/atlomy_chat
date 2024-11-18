#!/usr/bin/env python3

import os
import sys
import logging
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def stage_database_backup(
    s3_bucket='amta-app', 
    s3_prefix='amta-db',
    backup_dir='database_backups'
):
    """
    Stage database backup from S3 for future Docker deployment
    """
    logger.info(f"Starting database backup staging process")
    logger.info(f"S3 Bucket: {s3_bucket}")
    logger.info(f"S3 Prefix: {s3_prefix}")
    logger.info(f"Local Backup Directory: {backup_dir}")

    # Log environment variables for debugging
    logger.info("Environment Variables:")
    logger.info(f"EC2_INSTANCE_IP: {os.environ.get('EC2_INSTANCE_IP', 'NOT SET')}")
    logger.info(f"EC2_SSH_KEY_PATH: {os.environ.get('EC2_SSH_KEY_PATH', 'NOT SET')}")

    try:
        s3_client = boto3.client('s3')
        
        response = s3_client.list_objects_v2(
            Bucket=s3_bucket,
            Prefix=s3_prefix
        )
        
        backups = [obj['Key'] for obj in response.get('Contents', []) 
                   if obj['Key'].endswith('.tar.gz') or obj['Key'].endswith('.sql.gz')]
        
        if not backups:
            logger.warning("No database backups found in S3.")
            return False
        
        latest_backup = max(backups, key=lambda x: x.split('_')[-1])
        
        os.makedirs(backup_dir, exist_ok=True)
        local_backup_path = os.path.join(backup_dir, os.path.basename(latest_backup))
        
        s3_client.download_file(
            s3_bucket, 
            latest_backup, 
            local_backup_path
        )
        
        logger.info(f"Database backup downloaded: {local_backup_path}")
        
        # Prepare for EC2 transfer (placeholder for actual transfer logic)
        ec2_instance_ip = os.environ.get('EC2_INSTANCE_IP')
        ec2_ssh_key_path = os.environ.get('EC2_SSH_KEY_PATH')
        
        if ec2_instance_ip and ec2_ssh_key_path:
            logger.info("Preparing to transfer backup to EC2 instance")
            # TODO: Implement actual file transfer logic
            # This could use scp, aws ssm, or other transfer methods
            logger.warning("EC2 transfer not implemented in this version")
        else:
            logger.warning("EC2 instance transfer details not provided")
        
        logger.info("Backup ready for Docker deployment")
        return True
    
    except Exception as e:
        logger.error(f"Backup staging error: {e}")
        return False

def main():
    success = stage_database_backup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
