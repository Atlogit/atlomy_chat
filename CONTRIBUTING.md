# Contributing to Atlomy Chat

## Welcome Contributors!

Thank you for your interest in contributing to the Ancient Medical Texts Analysis App. This document provides guidelines for contributing to the project.

## Project Overview

Atlomy Chat is an advanced NLP research platform for analyzing ancient medical texts. Our goal is to create a robust, secure, and innovative tool for linguistic research.

## Contribution Workflow

### 1. Preparation

#### Prerequisites
- Git
- Python 3.9+
- Node.js 18+
- Docker
- AWS Account (for Bedrock and Secrets Manager)

#### Setup
1. Fork the repository
2. Clone your fork
```bash
git clone https://github.com/[YOUR_USERNAME]/atlomy_chat.git
cd atlomy_chat
```

3. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Development Guidelines

#### Branch Strategy
- `main`: Stable production code
- `develop`: Integration branch for upcoming release
- Feature branches: `feature/[descriptive-name]`
- Bugfix branches: `bugfix/[issue-description]`

#### Commit Messages
- Use clear, descriptive commit messages
- Follow conventional commit format:
  ```
  type(scope): description
  
  Examples:
  feat(secrets): add AWS Secrets Manager integration
  fix(deployment): resolve configuration validation issue
  docs(readme): update deployment workflow documentation
  ```

### 3. Code Quality

#### Style Guidelines
- Python: Follow PEP 8
- TypeScript/JavaScript: Use ESLint
- Use type annotations
- Write comprehensive docstrings

#### Testing
- Write unit tests for all new features
- Ensure 80%+ test coverage
- Run tests before submitting PR
```bash
# Backend tests
pytest tests/

# Frontend tests
cd next-app
npm test
```

### 4. Security Practices

#### Secrets Management
- NEVER commit sensitive information
- Use AWS Secrets Manager for credentials
- Follow least-privilege principle
- Use `config_validator.py` to validate configurations

#### Code Review Checklist
- No hardcoded credentials
- Proper error handling
- Input validation
- Secure AWS IAM role configurations

### 5. Configuration Management

#### Adding/Modifying Configurations
1. Update `.env.example` with new configuration keys
2. Modify `config_validator.py` to include new validation rules
3. Update documentation in `CONFIG_VALIDATOR.md`
4. Add tests for new configuration scenarios

### 6. Deployment Workflow Contributions

#### GitHub Actions
- Modifications to deployment workflows must:
  - Maintain security best practices
  - Support multiple deployment modes
  - Include comprehensive logging
  - Provide clear error reporting

#### Secrets Manager Integration
- Use dynamic secret retrieval
- Implement fallback mechanisms
- Support secret rotation
- Minimize API calls to Secrets Manager

### 7. Pull Request Process

#### PR Submission Checklist
- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Configuration validator passes
- [ ] Secrets management best practices followed

#### PR Template
```markdown
## Description
[Provide a clear description of changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
[Describe tests performed]

## Security Considerations
[Explain security measures implemented]
```

### 8. Review Process

#### Code Review Criteria
- Code quality
- Performance
- Security
- Documentation
- Test coverage
- Alignment with project goals

### 9. Reporting Issues

#### Bug Reports
- Use GitHub Issues
- Provide detailed description
- Include:
  - Steps to reproduce
  - Expected vs. actual behavior
  - Environment details
  - Logs/error messages

#### Feature Requests
- Explain the use case
- Provide potential implementation approach
- Discuss potential impact on existing system

### 10. Communication

#### Channels
- GitHub Issues
- Pull Request comments
- Project Slack channel

### 11. Code of Conduct

- Respect
- Collaboration
- Continuous learning
- Constructive feedback
- Inclusive environment

## Additional Resources

- [Secrets Management Guide](cline_docs/aws_secrets_manager_integration.md)
- [Configuration Validation](CONFIG_VALIDATOR.md)
- [Deployment Workflow](cline_docs/docker_github_actions_workflow.md)

## License

By contributing, you agree to the project's ISC License.

---

**Thank you for helping improve Atlomy Chat!** 🌟📚🔍
