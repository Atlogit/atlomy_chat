# AMTA GitHub Actions Workflows

## Overview
This project uses GitHub Actions for continuous integration, testing, and deployment across different environments.

## Workflow Types

### 1. Feature Branch Testing (feature-test.yml)
**Trigger**: Pull requests to main and production branches

**Checks Performed**:
- Python compatibility (3.10 and 3.11)
- Configuration validation
- Linting
- Code formatting
- Type checking
- Unit testing
- Security scanning

**Environment Setup**:
- PostgreSQL test database
- Redis test cache
- Simulated AWS Bedrock configuration

### 2. Staging Deployment (staging-deploy.yml)
**Trigger**: Pushes to main branch

**Checks Performed**:
- Run full test suite
- Configuration validation
- Build Docker image
- Deploy to staging ECS
- Slack notification on deployment status

**Environment**: Staging

### 3. Production Deployment (production-deploy.yml)
**Trigger**: Pushes to production branch

**Checks Performed**:
- AWS credentials validation
- Docker image build
- Push to Amazon ECR
- Deploy to production ECS
- Publish to PyPI
- Create GitHub Release

**Environment**: Production

## Prerequisites for Local Development

### Required Secrets
Configure these in GitHub repository settings:

#### For All Workflows
- `GITHUB_TOKEN`: GitHub Actions token

#### For Staging Deployment
- `STAGING_AWS_ACCESS_KEY_ID`
- `STAGING_AWS_SECRET_ACCESS_KEY`
- `SLACK_WEBHOOK`: Slack notification webhook

#### For Production Deployment
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `PYPI_USERNAME`
- `PYPI_PASSWORD`

## Best Practices

### Branch Protection
- Require status checks to pass before merging
- Enable required reviews
- Enforce linear history

### Workflow Customization
- Adjust Python versions as needed
- Modify test and deployment configurations
- Add additional checks or notifications

## Troubleshooting
- Check workflow logs for detailed error messages
- Verify secret configurations
- Ensure compatible dependency versions
- Test locally before pushing

## Performance Optimization
- Use caching for dependencies
- Minimize redundant checks
- Parallelize tests when possible

## Security Considerations
- Rotate credentials regularly
- Limit secret scope
- Use principle of least privilege
- Monitor workflow logs
