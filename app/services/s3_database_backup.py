import os
import logging
import boto3
import subprocess
from datetime import datetime
from app.core.secrets_manager import SecretsManager

class S3DatabaseBackupService:
    _RESTORE_FLAG_FILE = '/tmp/amta_db_restored.flag'

    def __init__(self, deployment_mode='development'):
        """
        Initialize S3 Database Backup Service
        
        :param deployment_mode: Current deployment environment
        """
        self.logger = logging.getLogger(__name__)
        self.deployment_mode = deployment_mode
        
        # Retrieve secrets from AWS Secrets Manager
        secrets = self._get_secrets()
        
        # S3 Configuration
        self.s3_bucket = secrets.get('S3_BACKUP_BUCKET', 'amta-app')
        self.s3_backup_prefix = secrets.get('S3_BACKUP_PREFIX', 'amta-db')
        
        # Database Configuration
        self.db_name = secrets.get('POSTGRES_DB', 'amta_greek')
        self.db_user = secrets.get('POSTGRES_USER')
        self.db_password = secrets.get('POSTGRES_PASSWORD')
        
        # S3 Client
        self.s3_client = boto3.client('s3')
    
    def _get_secrets(self):
        """
        Retrieve secrets for the current deployment mode
        
        :return: Dictionary of secrets
        """
        try:
            secrets_manager = SecretsManager()
            return secrets_manager.get_secrets(self.deployment_mode)
        except Exception as e:
            self.logger.error(f"Failed to retrieve secrets: {e}")
            return {}
    
    def is_database_restored(self):
        """
        Check if database has already been restored
        
        :return: Boolean indicating restoration status
        """
        return os.path.exists(self._RESTORE_FLAG_FILE)
    
    def mark_database_restored(self):
        """
        Mark database as restored by creating a flag file
        """
        try:
            with open(self._RESTORE_FLAG_FILE, 'w') as f:
                f.write(datetime.now().isoformat())
            self.logger.info("Database restoration flag set")
        except Exception as e:
            self.logger.error(f"Failed to set restoration flag: {e}")
    
    def reset_restoration_status(self):
        """
        Reset the database restoration status
        Useful for forcing a new restoration
        """
        try:
            if os.path.exists(self._RESTORE_FLAG_FILE):
                os.remove(self._RESTORE_FLAG_FILE)
            self.logger.info("Database restoration flag reset")
        except Exception as e:
            self.logger.error(f"Failed to reset restoration flag: {e}")
    
    def download_latest_backup(self, local_backup_dir='database_backups'):
        """
        Download the latest database backup from S3
        
        :param local_backup_dir: Local directory to save backup
        :return: Path to downloaded backup
        """
        try:
            # List objects in S3 bucket
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=self.s3_backup_prefix
            )
            
            # Find the latest backup file
            backups = [obj['Key'] for obj in response.get('Contents', []) 
                       if obj['Key'].endswith('.tar.gz') or obj['Key'].endswith('.sql.gz')]
            
            if not backups:
                self.logger.error("No database backups found in S3.")
                return None
            
            latest_backup = max(backups, key=lambda x: x.split('_')[-1])
            
            # Create local backup directory
            os.makedirs(local_backup_dir, exist_ok=True)
            local_backup_path = os.path.join(local_backup_dir, os.path.basename(latest_backup))
            
            # Download backup
            self.s3_client.download_file(
                self.s3_bucket, 
                latest_backup, 
                local_backup_path
            )
            
            self.logger.info(f"Downloaded backup: {local_backup_path}")
            return local_backup_path
        
        except Exception as e:
            self.logger.error(f"Error downloading database backup: {e}")
            return None
    
    def restore_database_backup(self, backup_path=None):
        """
        Restore database from S3 backup
        
        :param backup_path: Path to database backup file. If None, downloads latest.
        :return: Boolean indicating restoration success
        """
        # Check if database has already been restored
        if self.is_database_restored():
            self.logger.info("Database already restored. Skipping restoration.")
            return True
        
        try:
            # If no backup path provided, download latest
            if not backup_path:
                backup_path = self.download_latest_backup()
            
            if not backup_path:
                self.logger.error("No backup file available for restoration")
                return False
            
            # Drop and recreate database
            drop_db_cmd = [
                'psql', 
                '-h', 'localhost', 
                '-U', self.db_user, 
                '-c', f'DROP DATABASE IF EXISTS "{self.db_name}";'
            ]
            
            create_db_cmd = [
                'psql', 
                '-h', 'localhost', 
                '-U', self.db_user, 
                '-c', f'CREATE DATABASE "{self.db_name}";'
            ]
            
            restore_cmd = [
                'pg_restore' if backup_path.endswith('.tar.gz') else 'psql',
                '-h', 'localhost',
                '-U', self.db_user,
                '-d', self.db_name,
                backup_path
            ]
            
            # Environment for authentication
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_password
            
            # Execute commands
            subprocess.run(drop_db_cmd, env=env, check=True)
            subprocess.run(create_db_cmd, env=env, check=True)
            subprocess.run(restore_cmd, env=env, check=True)
            
            # Mark database as restored
            self.mark_database_restored()
            
            self.logger.info(f"Database {self.db_name} restored successfully")
            return True
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Database restoration error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during database restoration: {e}")
            return False
