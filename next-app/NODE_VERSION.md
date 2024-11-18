# Node.js Version Management

## Recommended Node.js Version
- **Stable Version**: 20.18.0
- **Minimum Compatible Version**: 18.x
- **Maximum Tested Version**: 20.x

## Version Management

### Using NVM
```bash
nvm install 20.18.0
nvm use 20.18.0
nvm alias default 20.18.0
```

### Docker Configuration
- Base Image: node:20.18.0-alpine
- Ensure Dockerfile uses matching version

## Troubleshooting
- If experiencing build issues, verify:
  1. Node.js version matches Dockerfile
  2. npm version is compatible
  3. All dependencies support the Node.js version
