# AMTA Deployment Walkthrough: From Local Development to AWS EC2

## Key Deployment Mechanism
- GitHub Actions handles file transfer to EC2
- No manual git clone required on EC2 instance
- Automated deployment process

## Deployment Process Overview
1. Local Development and Image Preparation
2. GitHub Actions Workflow Triggers Deployment
3. Automated File Transfer to EC2
4. Docker Image Deployment
5. Service Startup and Verification

## Prerequisites
- GitHub account with repository access
- AWS Account
- AWS CLI configured
- Docker installed locally
- GitHub CLI (optional but recommended)
- SSH key for EC2 access

## Step 1: Local Repository Preparation
```bash
# Clone the repository locally
git clone https://github.com/your-org/atlomy_chat.git
cd atlomy_chat

# Verify initial setup
ls  # Confirm key files exist:
# - Dockerfile
# - docker-compose.yml
# - deploy_manager.sh
# - .env.example
```

## Step 2: Environment Configuration
1. Create `.env` files
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your specific configurations
nano .env

# Key configurations to set:
# - REDIS_URL
# - DATABASE_URL
# - AWS_REGION
# - BEDROCK_MODEL_ID
```

## Step 3: Local Deployment Validation
```bash
# Make deployment scripts executable
chmod +x deploy_manager.sh deployment_readiness.sh verify_deployment.sh

# Run deployment readiness checks
./deploy_manager.sh local verify

# Run local deployment
./deploy_manager.sh local deploy
```

## Step 4: Docker Image Preparation
```bash
# Build Docker images
docker build -t atlomy-backend -f Dockerfile.backend .
docker build -t atlomy-frontend -f next-app/Dockerfile ./next-app

# Tag images for GitHub Container Registry
GITHUB_REPO=your-github-username/atlomy_chat
docker tag atlomy-backend ghcr.io/${GITHUB_REPO}-backend:production
docker tag atlomy-frontend ghcr.io/${GITHUB_REPO}-frontend:production

# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u your-github-username --password-stdin

# Push images
docker push ghcr.io/${GITHUB_REPO}-backend:production
docker push ghcr.io/${GITHUB_REPO}-frontend:production
```

## Step 5: AWS EC2 Preparation
1. Create EC2 Instance
   - Amazon Linux 2 or Ubuntu
   - t2.medium or larger
   - Security Group:
     * Allow SSH (port 22)
     * Allow HTTP (port 80)
     * Allow HTTPS (port 443)
     * Allow application ports (8081, 3000)

2. Install Dependencies on EC2
```bash
# SSH into EC2 instance (for initial setup only)
ssh -i your-key.pem ec2-user@your-ec2-instance

# Update system
sudo yum update -y  # For Amazon Linux
# OR
sudo apt update -y  # For Ubuntu

# Install Docker
sudo yum install docker -y  # Amazon Linux
# OR
sudo apt install docker.io -y  # Ubuntu

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Step 6: GitHub Actions Deployment
1. Configure GitHub Secrets
   - `AWS_OIDC_ROLE_ARN`: AWS IAM Role ARN
   - `EC2_SSH_PRIVATE_KEY`: Base64 encoded SSH private key
   - `EC2_HOST`: EC2 instance public DNS/IP
   - `EC2_USER`: EC2 login user (ec2-user or ubuntu)

2. Trigger Deployment
```bash
# Option 1: Manual GitHub Actions trigger
gh workflow run production-deploy.yml

# Option 2: Push to production branch
git checkout production
git push origin production
```

## Deployment Workflow Details
- GitHub Actions automatically:
  * Transfers docker-compose.yml
  * Transfers .env file
  * Pulls Docker images
  * Starts services on EC2
- NO manual git clone required on EC2

## Step 7: Deployment Verification
```bash
# Verify deployment via GitHub Actions logs
# Check workflow run in GitHub repository

# Optional: SSH to verify (not required)
ssh -i your-key.pem ec2-user@your-ec2-instance
docker-compose ps
```

## Troubleshooting
- Check GitHub Actions workflow logs
- Verify AWS Secrets Manager configuration
- Check network security groups
- Validate Docker network settings

## Maintenance
- Update `.env` configurations
- Rotate AWS credentials
- Monitor deployment logs
- Keep dependencies updated

## Additional Resources
- [Deployment Strategy](DEPLOYMENT_STRATEGY.md)
- [Deployment Integration Guide](DEPLOYMENT_INTEGRATION.md)
- [Deployment Verification Checklist](DEPLOYMENT_VERIFICATION_CHECKLIST.md)
