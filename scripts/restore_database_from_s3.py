#!/usr/bin/env python3

import os
import sys
import boto3
import psycopg2
import subprocess

def database_exists(db_name, db_user, db_password, host='localhost'):
    """
    Check if a specific database exists
    
    :param db_name: Name of the database
    :param db_user: Database user
    :param db_password: Database password
    :param host: Database host
    :return: Boolean indicating database existence
    """
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=db_user,
            password=db_password,
            host=host
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{db_name}'")
        return cur.fetchone() is not None
    except Exception as e:
        print(f"Error checking database existence: {e}")
        return False

def restore_database_from_s3(
    db_name='amta_greek', 
    db_user='atlomy', 
    db_password='atlomy21',
    s3_bucket='amta-app', 
    s3_prefix='amta-db'
):
    """
    Restore database from S3 backup
    
    :param db_name: Target database name
    :param db_user: Database user
    :param db_password: Database password
    :param s3_bucket: S3 bucket name
    :param s3_prefix: S3 prefix/folder for backups
    :return: Boolean indicating restoration success
    """
    try:
        # Check if database already exists
        if database_exists(db_name, db_user, db_password):
            print(f"Database {db_name} already exists. Skipping restoration.")
            return True
        
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # List objects in S3 bucket
        response = s3_client.list_objects_v2(
            Bucket=s3_bucket,
            Prefix=s3_prefix
        )
        
        # Find the latest backup file
        backups = [obj['Key'] for obj in response.get('Contents', []) 
                   if obj['Key'].endswith('.tar.gz') or obj['Key'].endswith('.sql.gz')]
        
        if not backups:
            print("No database backups found in S3.")
            return False
        
        latest_backup = max(backups, key=lambda x: x.split('_')[-1])
        
        # Create local backup directory
        os.makedirs('database_backups', exist_ok=True)
        local_backup_path = os.path.join('database_backups', os.path.basename(latest_backup))
        
        # Download backup
        s3_client.download_file(
            s3_bucket, 
            latest_backup, 
            local_backup_path
        )
        
        # Prepare environment for authentication
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        # Drop and recreate database commands
        drop_db_cmd = [
            'psql', 
            '-h', 'localhost', 
            '-U', db_user, 
            '-c', f'DROP DATABASE IF EXISTS "{db_name}";'
        ]
        
        create_db_cmd = [
            'psql', 
            '-h', 'localhost', 
            '-U', db_user, 
            '-c', f'CREATE DATABASE "{db_name}";'
        ]
        
        # Restore command (different for .tar.gz and .sql.gz)
        restore_cmd = [
            'pg_restore' if local_backup_path.endswith('.tar.gz') else 'psql',
            '-h', 'localhost',
            '-U', db_user,
            '-d', db_name,
            local_backup_path
        ]
        
        # Execute database restoration commands
        subprocess.run(drop_db_cmd, env=env, check=True)
        subprocess.run(create_db_cmd, env=env, check=True)
        subprocess.run(restore_cmd, env=env, check=True)
        
        print(f"Database {db_name} restored successfully")
        return True
    
    except Exception as e:
        print(f"Database restoration error: {e}")
        return False

def main():
    """
    Main entry point for script
    Allows direct execution with optional configuration
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Restore database from S3')
    parser.add_argument('--db-name', default='amta_greek', help='Database name')
    parser.add_argument('--db-user', default='atlomy', help='Database user')
    parser.add_argument('--db-password', default='atlomy21', help='Database password')
    parser.add_argument('--s3-bucket', default='amta-app', help='S3 bucket name')
    parser.add_argument('--s3-prefix', default='amta-db', help='S3 prefix/folder')
    
    args = parser.parse_args()
    
    success = restore_database_from_s3(
        db_name=args.db_name,
        db_user=args.db_user,
        db_password=args.db_password,
        s3_bucket=args.s3_bucket,
        s3_prefix=args.s3_prefix
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
