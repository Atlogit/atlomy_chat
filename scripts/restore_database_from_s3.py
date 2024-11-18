#!/usr/bin/env python3

import os
import sys
import logging
import subprocess
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def transfer_to_ec2(local_backup_path):
    """
    Transfer backup to EC2 instance using AWS CLI
    """
    # Retrieve EC2 and S3 details from environment
    ec2_instance_id = os.environ.get('EC2_INSTANCE_ID')
    s3_bucket = os.environ.get('S3_BACKUP_BUCKET', 'amta-app')
    
    if not ec2_instance_id:
        logger.warning("No EC2 instance ID provided. Skipping transfer.")
        return False

    try:
        # Use AWS CLI to copy file to EC2 instance
        transfer_cmd = [
            'aws', 'ssm', 'send-command',
            '--instance-ids', ec2_instance_id,
            '--document-name', 'AWS-RunShellScript',
            '--parameters', f'commands=["mkdir -p /opt/atlomy/database_backups", "aws s3 cp s3://{s3_bucket}/{os.path.basename(local_backup_path)} /opt/atlomy/database_backups/latest_backup.tar.gz"]'
        ]
        
        result = subprocess.run(transfer_cmd, capture_output=True, text=True, check=True)
        
        logger.info("Backup transfer command sent successfully")
        logger.info(f"Transfer output: {result.stdout}")
        
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Transfer failed: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected transfer error: {e}")
        return False

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
        
        # Attempt to transfer to EC2
        transfer_success = transfer_to_ec2(local_backup_path)
        
        if transfer_success:
            logger.info("Backup transferred to EC2 instance")
        else:
            logger.warning("Failed to transfer backup to EC2 instance")
        
        return True
    
    except Exception as e:
        logger.error(f"Backup staging error: {e}")
        return False

def main():
    success = stage_database_backup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
