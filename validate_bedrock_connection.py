#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
import os
import sys

def load_aws_credentials():
    """Load AWS credentials from .aws_credentials file"""
    credentials = {}
    with open('.aws_credentials', 'r') as f:
        for line in f:
            if line.startswith('export '):
                key, value = line.strip().split('=', 1)
                credentials[key.replace('export ', '')] = value.strip()
    return credentials

def validate_bedrock_connection():
    """
    Comprehensive Bedrock connection and model validation
    """
    print("🔍 Bedrock Connection Diagnostic Tool")
    print("====================================")
    
    try:
        # Load credentials
        credentials = load_aws_credentials()
        
        # Validate credential presence
        if not credentials.get('AWS_ACCESS_KEY_ID') or not credentials.get('AWS_SECRET_ACCESS_KEY'):
            print("❌ Incomplete AWS credentials")
            return False
        
        # Create Bedrock client
        bedrock_client = boto3.client(
            'bedrock', 
            region_name='us-east-1',
            aws_access_key_id=credentials['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=credentials['AWS_SECRET_ACCESS_KEY']
        )
        
        # List available foundation models
        try:
            models = bedrock_client.list_foundation_models()
            
            print("✅ Bedrock Connection Successful")
            print("\n🤖 Available Foundation Models:")
            for model in models['modelSummaries']:
                print(f"- {model['modelId']}")
                if 'claude-3' in model['modelId']:
                    print(f"  Provider: {model.get('providerName', 'Unknown')}")
                    print(f"  Input Modalities: {model.get('inputModalities', [])}")
                    print(f"  Output Modalities: {model.get('outputModalities', [])}")
            
            return True
        
        except ClientError as model_error:
            print(f"❌ Model Access Error: {model_error}")
            return False
    
    except (NoCredentialsError, PartialCredentialsError) as cred_error:
        print(f"❌ Credential Error: {cred_error}")
        return False
    
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def main():
    success = validate_bedrock_connection()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
