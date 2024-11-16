# Ancient Medical Texts Analysis App

A comprehensive application for analyzing ancient medical texts using modern NLP and LLM technologies.

## Features

- **Lexical Value Management**: Create, update, and analyze lexical values from ancient medical texts
- **LLM-Powered Analysis**: Analyze terms using AWS Bedrock (Claude-3) with contextual understanding
- **Redis Caching**: Efficient caching system for improved performance
- **Modern Frontend**: React-based UI with Tailwind CSS and DaisyUI
- **Secure Configuration Management**: AWS Secrets Manager integration
- **Automated Deployment**: Docker and GitHub Actions CI/CD

## Secrets and Configuration Management

### Secrets Management
We use AWS Secrets Manager for comprehensive, secure secret management:
- Encrypted secret storage for all sensitive credentials
- Dynamic secret retrieval across multiple environments
- Environment-specific configurations
- Automatic secret rotation support
- Centralized management of:
  * Database credentials
  * Redis connection details
  * AWS Bedrock configuration
  * Other sensitive configuration parameters

#### Advanced Credential Handling
- PostgreSQL database credentials securely managed
- Separate secrets for development, staging, and production
- Granular access control for different deployment modes

### Configuration Validation
- Comprehensive automated checks for deployment configurations
- Validation of secret structures across environments
- Advanced security checks:
  * Password complexity verification
  * Secure host configuration validation
  * Environment-specific credential requirements
- Detailed error logging and reporting
- Prevents deployment with incomplete or insecure configurations

### Deployment Modes
- `development`: Local development environment with minimal security constraints
- `staging`: Pre-production testing with enhanced security checks
- `production`: Strict security validation and comprehensive credential protection

#### Validation Checks
- Secret structure integrity
- Deployment mode-specific configuration
- Database credential validation
- AWS Secrets Manager connectivity
- Password complexity enforcement
- Secure host configuration

## Deployment Architecture

### CI/CD Workflow
1. Code Commit to GitHub
2. Automated Testing
3. Docker Image Build
4. Image Push to GitHub Container Registry
5. Comprehensive Configuration Validation
6. Secrets Retrieval from AWS Secrets Manager
7. Secure Deployment to EC2 Instance

### Security Practices
- No hardcoded credentials
- Secrets encrypted at rest
- Least-privilege IAM roles
- Regular secret rotation
- Comprehensive access logging
- Environment-specific security constraints

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- AWS Account with Bedrock access

## Setup

### 1. Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/Atlogit/atlomy_chat.git
cd atlomy_chat
```

2. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install Node.js dependencies:
```bash
cd next-app
npm install
```

### 2. Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Configure your environment variables in `.env`:
   - Database settings
   - AWS Bedrock credentials
   - Redis connection details
   - LLM parameters

### 3. AWS Bedrock Setup

1. Ensure you have AWS credentials with Bedrock access
2. Configure your AWS credentials in `.env`:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

### 4. Database Setup

1. Create the PostgreSQL database:
```bash
createdb amta
```

2. Run database migrations:
```bash
alembic upgrade head
```

### 5. Redis Setup

1. Install Redis:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
```

2. Start Redis:
```bash
# Ubuntu/Debian
sudo systemctl start redis

# macOS
brew services start redis
```

## Configuration Validation

### Running Configuration Validator
```bash
# Validate configuration
python config_validator.py

# Validate with specific environment file
python config_validator.py .env.development
```

### Validation Checks
- Secret structure integrity
- Deployment mode validation
- Environment-specific configuration
- AWS Secrets Manager connectivity

## Running the Application

1. Start the FastAPI backend:
```bash
uvicorn app.run_server:app --reload
```

2. Start the Next.js frontend:
```bash
cd next-app
npm run dev
```

3. Access the application at `http://localhost:3000`

## Using the Components

### Lexical Value Management

1. Navigate to the Lexical Values section
2. Use the interface to:
   - Create new lexical values
   - Update existing entries
   - View and manage translations
   - Add categories and references

### LLM Analysis

1. Navigate to the Term Analysis section
2. Enter a term to analyze
3. Add relevant contexts:
   - Text passages
   - Author information
   - References
4. Choose analysis options:
   - Stream response (real-time updates)
   - Token count monitoring
5. View and save analysis results

## Monitoring and Logging

### Deployment Monitoring
- AWS CloudWatch logs
- GitHub Actions status checks
- Slack deployment notifications
- Prometheus metrics integration

### Performance Tracking
- Application performance metrics
- Deployment time tracking
- Error rate monitoring
- Resource utilization insights

## Testing

1. Run backend tests:
```bash
pytest tests/
```

2. Run frontend tests:
```bash
cd next-app
npm test
```

3. Run integration tests:
```bash
pytest tests/test_integration.py
```

## Caching Behavior

- Text data: 24-hour TTL
- Search results: 30-minute TTL
- Analysis results: 1-hour TTL

Cache invalidation occurs automatically when:
- Lexical values are updated
- New analyses are generated
- Token limits are exceeded

## Troubleshooting

### Common Issues

1. AWS Bedrock Connection:
   - Verify AWS credentials
   - Check region settings
   - Ensure Bedrock model access

2. Redis Connection:
   - Verify Redis is running
   - Check connection settings
   - Monitor memory usage

3. Database Issues:
   - Check connection string
   - Verify migrations
   - Monitor connection pool

4. Secrets and Configuration
   - Verify IAM role permissions
   - Check AWS Secrets Manager access
   - Validate configuration validator results

### Logs

- Backend logs: `logs/app.log`
- Redis logs: System default location
- Frontend logs: Browser console
- Deployment logs: GitHub Actions and AWS CloudWatch

## Troubleshooting Configuration and Secrets

### Common Issues
1. AWS Secrets Manager Access
   - Verify IAM role permissions
   - Check network connectivity
   - Validate AWS credentials

2. Configuration Validation Failures
   - Review secret structure
   - Check deployment mode
   - Verify environment variables

3. Deployment Workflow Problems
   - Inspect GitHub Actions logs
   - Check Docker image build logs
   - Validate EC2 instance configuration

### Debugging Tools
- `config_validator.py`: Comprehensive configuration checks
- AWS CloudTrail: Secret access logging
- GitHub Actions logs: Deployment workflow insights

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

### Contributing to Configuration Management
1. Follow security best practices
2. Update documentation with configuration changes
3. Implement comprehensive test coverage
4. Review IAM and secret management approaches

## Additional Documentation
- [Secrets Management Guide](cline_docs/aws_secrets_manager_integration.md)
- [Configuration Validation](CONFIG_VALIDATOR.md)
- [Deployment Workflow](cline_docs/docker_github_actions_workflow.md)

## License

ISC License - See LICENSE file for details
