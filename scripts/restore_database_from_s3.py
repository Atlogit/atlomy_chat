#!/usr/bin/env python3

import os
import sys
import logging
import socket
import boto3
import psycopg2
import subprocess
from botocore.exceptions import ClientError
from botocore.config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_port_open(host, port, timeout=5):
    """Check if a specific host:port is reachable."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.error(f"Port check error for {host}:{port}: {e}")
        return False

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
            return boto3.client('s3', config=Config(
                retries={'max_attempts': 3, 'mode': 'standard'}
            ))
        except Exception as default_error:
            logger.error(f"S3 client creation failed: {default_error}")
            return None

def get_env_var(name, default=None, required=False):
    """Safely retrieve environment variables with optional defaults."""
    value = os.environ.get(name, default)
    if required and not value:
        raise ValueError(f"Required environment variable {name} is not set")
    return value

def stage_database_backup(
    s3_bucket=None, 
    s3_prefix='amta-db',
    backup_dir='database_backups'
):
    """
    Stage database backup from S3 without attempting restoration
    Prepares backup for future use during Docker deployment
    """
    # Use environment variables with fallback to parameters
    s3_bucket = s3_bucket or get_env_var('S3_BACKUP_BUCKET', 'amta-app')
    deployment_mode = get_env_var('DEPLOYMENT_MODE', 'production')

    logger.info(f"Starting database backup staging process")
    logger.info(f"Deployment Mode: {deployment_mode}")
    logger.info(f"S3 Bucket: {s3_bucket}")
    logger.info(f"S3 Prefix: {s3_prefix}")

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

def database_exists(db_name, db_user, db_password, host='localhost', port=5432):
    """Check if a specific database exists with comprehensive error handling."""
    logger.info(f"Checking database existence: {db_name} on {host}:{port}")
    
    # First, check if port is open
    if not check_port_open(host, port):
        logger.error(f"PostgreSQL port {port} on {host} is not accessible")
        return False

    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=db_user,
            password=db_password,
            host=host,
            port=port,
            connect_timeout=10  # Add connection timeout
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
            exists = cur.fetchone() is not None
            logger.info(f"Database {db_name} exists: {exists}")
            return exists
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        logger.error(f"Connection details - Host: {host}, Port: {port}, User: {db_user}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking database: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def restore_database_from_s3(
    db_name=None, 
    db_user=None, 
    db_password=None,
    db_host='localhost',
    db_port=5432,
    s3_bucket=None, 
    s3_prefix='amta-db',
    max_retries=3
):
    """Robust database restoration from S3 with improved error handling and configurability."""
    # Use environment variables with fallback to parameters
    db_name = db_name or get_env_var('DB_NAME', 'amta_greek')
    db_user = db_user or get_env_var('DB_USER', 'atlomy')
    db_password = db_password or get_env_var('DB_PASSWORD')
    s3_bucket = s3_bucket or get_env_var('S3_BACKUP_BUCKET', 'amta-app')
    db_host = get_env_var('DB_HOST', db_host)
    
    # Safely handle DB_PORT, defaulting to 5432 if not set or empty
    try:
        db_port = int(os.environ.get('DB_PORT', str(db_port)) or 5432)
    except ValueError:
        logger.warning(f"Invalid DB_PORT, defaulting to {db_port}")
        db_port = 5432

    logger.info(f"Starting database restoration process")
    logger.info(f"Configuration - Host: {db_host}, Port: {db_port}, Database: {db_name}")

    if not db_password:
        logger.error("Database password is required")
        return False

    try:
        # Check if database already exists
        if database_exists(db_name, db_user, db_password, host=db_host, port=db_port):
            logger.info(f"Database {db_name} already exists. Skipping restoration.")
            return True
        
        # Stage backup first
        if not stage_database_backup(s3_bucket, s3_prefix):
            logger.error("Failed to stage database backup")
            return False
        
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
        os.makedirs('database_backups', exist_ok=True)
        local_backup_path = os.path.join('database_backups', os.path.basename(latest_backup))
        
        # Prepare environment for authentication
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        # Drop and recreate database commands
        drop_db_cmd = [
            'psql', 
            '-h', db_host, 
            '-p', str(db_port),
            '-U', db_user, 
            '-c', f'DROP DATABASE IF EXISTS "{db_name}";'
        ]
        
        create_db_cmd = [
            'psql', 
            '-h', db_host, 
            '-p', str(db_port),
            '-U', db_user, 
            '-c', f'CREATE DATABASE "{db_name}";'
        ]
        
        # Restore command (different for .tar.gz and .sql.gz)
        restore_cmd = [
            'pg_restore' if local_backup_path.endswith('.tar.gz') else 'psql',
            '-h', db_host,
            '-p', str(db_port),
            '-U', db_user,
            '-d', db_name,
            local_backup_path
        ]
        
        # Execute database restoration commands
        for cmd in [drop_db_cmd, create_db_cmd, restore_cmd]:
            try:
                result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
                logger.info(f"Command executed successfully: {' '.join(cmd)}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Command failed: {' '.join(cmd)}")
                logger.error(f"STDOUT: {e.stdout}")
                logger.error(f"STDERR: {e.stderr}")
                return False
        
        logger.info(f"Database {db_name} restored successfully")
        return True
    
    except Exception as e:
        logger.error(f"Unexpected error during database restoration: {e}")
        return False

def main():
    """
    Main entry point for script
    Allows direct execution with optional configuration
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Restore database from S3')
    parser.add_argument('--db-name', help='Database name')
    parser.add_argument('--db-user', help='Database user')
    parser.add_argument('--db-password', help='Database password')
    parser.add_argument('--db-host', help='Database host')
    parser.add_argument('--db-port', type=int, help='Database port')
    parser.add_argument('--s3-bucket', help='S3 bucket name')
    parser.add_argument('--s3-prefix', help='S3 prefix/folder')
    parser.add_argument('--stage-only', action='store_true', help='Only stage backup, do not restore')
    
    args = parser.parse_args()
    
    # Determine whether to stage only or perform full restoration
    if args.stage_only:
        success = stage_database_backup(
            s3_bucket=args.s3_bucket,
            s3_prefix=args.s3_prefix or 'amta-db'
        )
    else:
        # Use environment variables if not provided via arguments
        success = restore_database_from_s3(
            db_name=args.db_name,
            db_user=args.db_user,
            db_password=args.db_password,
            db_host=args.db_host,
            db_port=args.db_port,
            s3_bucket=args.s3_bucket,
            s3_prefix=args.s3_prefix
        )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
