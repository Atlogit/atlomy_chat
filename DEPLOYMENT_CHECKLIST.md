# AMTA Deployment Checklist: Step-by-Step Verification

## Prerequisite Checklist
### 1. Local Environment Setup
- [ ] Git is installed
- [ ] GitHub CLI is installed (optional)
- [ ] AWS CLI is configured
- [ ] SSH key is generated for EC2 access

## Step-by-Step Deployment Process

### Step 1: Repository Preparation
- [ ] Clone repository
  ```bash
  git clone https://github.com/your-org/atlomy_chat.git
  cd atlomy_chat
  ```
- [ ] Verify key files exist
  ```bash
  ls  # Check for:
  # - Dockerfile.backend
  # - next-app/Dockerfile
  # - docker-compose.yml
  # - .env.example
  ```

### Step 2: Environment Configuration
- [ ] Create .env file
  ```bash
  cp .env.example .env
  ```
- [ ] Edit .env file
  - [ ] Set REDIS_URL
  - [ ] Set DATABASE_URL
  - [ ] Set AWS_REGION
  - [ ] Set BEDROCK_MODEL_ID
- [ ] Verify configuration
  ```bash
  cat .env  # Double-check settings
  ```

### Step 3: Automated Docker Image Build
- [ ] Ensure GitHub Actions is configured
  - [ ] Workflow triggers on push to production branch
  - [ ] Docker Build and Registry Push workflow exists
- [ ] Trigger image build
  ```bash
  # Option 1: Push to production branch
  git checkout production
  git push origin production

  # Option 2: Manual workflow dispatch
  gh workflow run docker-deploy.yml
  ```
- [ ] Verify image build
  - [ ] Check GitHub Actions workflow logs
  - [ ] Confirm images pushed to GitHub Container Registry

### Step 4: AWS EC2 Preparation
- [ ] Create EC2 Instance
  - [ ] Choose Amazon Linux 2 or Ubuntu
  - [ ] Select t2.medium or larger
  - [ ] Configure Security Group
    * Allow SSH (port 22)
    * Allow HTTP (port 80)
    * Allow HTTPS (port 443)
    * Allow application ports (8081, 3000)
- [ ] Install Docker on EC2
  ```bash
  # For Amazon Linux
  sudo yum update -y
  sudo yum install docker -y
  sudo systemctl start docker
  sudo systemctl enable docker

  # For Ubuntu
  sudo apt update -y
  sudo apt install docker.io -y
  sudo systemctl start docker
  sudo systemctl enable docker
  ```
- [ ] Install Docker Compose
  ```bash
  sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  ```

### Step 5: GitHub Actions Configuration
- [ ] Configure GitHub Secrets
  - [ ] `AWS_OIDC_ROLE_ARN`: AWS IAM Role ARN
  - [ ] `EC2_SSH_PRIVATE_KEY`: Base64 encoded SSH private key
  - [ ] `EC2_HOST`: EC2 instance public DNS/IP
  - [ ] `EC2_USER`: EC2 login user (ec2-user or ubuntu)
  - [ ] `PAT`: Personal Access Token for workflow triggers

### Step 6: Deployment Trigger
- [ ] Trigger Production Deployment
  ```bash
  # Option 1: Manual GitHub Actions trigger
  gh workflow run production-deploy.yml

  # Option 2: Automatic trigger after image build
  # (Docker Build workflow will automatically trigger production deploy)
  ```

### Step 7: Deployment Verification
- [ ] Check GitHub Actions workflow logs
  - [ ] Verify Docker Build workflow
  - [ ] Confirm Production Deploy workflow
- [ ] Verify Docker services on EC2
  ```bash
  # Optional SSH verification
  ssh -i your-key.pem ec2-user@your-ec2-instance
  docker-compose ps
  ```
- [ ] Test Application Endpoints
  - [ ] Backend health check: `http://your-ec2-ip:8081/health`
  - [ ] Frontend accessibility: `http://your-ec2-ip:3000`

## Troubleshooting Checklist
- [ ] Review GitHub Actions workflow logs
- [ ] Check AWS Secrets Manager configuration
- [ ] Verify network security groups
- [ ] Validate Docker network settings
- [ ] Confirm GitHub Container Registry access

## Post-Deployment Recommendations
- [ ] Monitor application logs
- [ ] Set up additional monitoring
- [ ] Regularly update dependencies
- [ ] Rotate AWS credentials

## Success Criteria
- [ ] Docker images successfully built
- [ ] Images pushed to GitHub Container Registry
- [ ] GitHub Actions deployment successful
- [ ] Application endpoints responsive
- [ ] Database connectivity verified

## Additional Resources
- [Deployment Strategy](DEPLOYMENT_STRATEGY.md)
- [Deployment Integration Guide](DEPLOYMENT_INTEGRATION.md)
- [Deployment Verification Checklist](DEPLOYMENT_VERIFICATION_CHECKLIST.md)
