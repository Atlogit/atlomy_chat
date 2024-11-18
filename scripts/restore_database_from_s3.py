#!/usr/bin/env python3

import os
import sys
import logging
import subprocess
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def transfer_backup_via_ssh(local_backup_path):
    """
    Transfer backup to EC2 instance using SSH
    """
    # Retrieve SSH connection details
    ec2_host = os.environ.get('EC2_HOST')
    ec2_user = os.environ.get('EC2_USER', 'ec2-user')
    ssh_key_path = os.environ.get('EC2_SSH_PRIVATE_KEY_PATH', '/tmp/ec2_ssh_key')
    
    if not ec2_host:
        logger.error("No EC2 host specified for SSH transfer")
        return False
    
    # Ensure SSH key is available
    if not os.path.exists(ssh_key_path):
        try:
            # Write SSH key from environment variable
            ssh_key = os.environ.get('EC2_SSH_PRIVATE_KEY')
            if not ssh_key:
                logger.error("No SSH private key provided")
                return False
            
            with open(ssh_key_path, 'w') as key_file:
                key_file.write(ssh_key)
            
            # Set correct permissions for SSH key
            os.chmod(ssh_key_path, 0o600)
        except Exception as e:
            logger.error(f"Failed to write SSH key: {e}")
            return False
    
    # Destination directory for database backup staging
    remote_backup_dir = '/opt/atlomy/database_backups'
    
    try:
        # Ensure remote directory exists with correct permissions
        ssh_mkdir_cmd = [
            'ssh', 
            '-o', 'StrictHostKeyChecking=no',
            '-i', ssh_key_path,
            f'{ec2_user}@{ec2_host}',
            f'mkdir -p {remote_backup_dir} && chmod 755 {remote_backup_dir}'
        ]
        
        subprocess.run(ssh_mkdir_cmd, check=True)
        
        # SCP command to transfer backup
        scp_cmd = [
            'scp', 
            '-o', 'StrictHostKeyChecking=no',
            '-i', ssh_key_path,
            local_backup_path,
            f'{ec2_user}@{ec2_host}:{remote_backup_dir}/latest_backup.tar.gz'
        ]
        
        # Execute SCP transfer
        result = subprocess.run(scp_cmd, capture_output=True, text=True, check=True)
        
        logger.info("Backup transferred via SSH successfully")
        logger.info(f"Transfer command: {' '.join(scp_cmd)}")
        logger.info(f"Remote backup directory: {remote_backup_dir}")
        
        # Optional: Verify file on remote system
        ssh_verify_cmd = [
            'ssh', 
            '-o', 'StrictHostKeyChecking=no',
            '-i', ssh_key_path,
            f'{ec2_user}@{ec2_host}',
            f'ls -l {remote_backup_dir}/latest_backup.tar.gz'
        ]
        
        verify_result = subprocess.run(ssh_verify_cmd, capture_output=True, text=True, check=True)
        logger.info(f"Remote file verification: {verify_result.stdout.strip()}")
        
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"SSH transfer failed: {e}")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected SSH transfer error: {e}")
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
        
        # Transfer backup via SSH
        transfer_success = transfer_backup_via_ssh(local_backup_path)
        
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
