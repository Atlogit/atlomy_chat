# Node.js Version Requirements

## Supported Node.js Versions

This project requires Node.js version 20.18.0.

### Why This Version?

Many of our dependencies have specific Node.js version requirements:
- Next.js 15.0.1 requires Node.js >=18.18.0
- TypeScript 5.6.3 requires Node.js >=14.17
- Testing libraries require Node.js >=16 or >=18

## Managing Node.js Version

We recommend using `nvm` (Node Version Manager) to manage Node.js versions:

```bash
# Install NVM (if not already installed)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash

# Install the required Node.js version
nvm install 20.18.0

# Use the required version
nvm use 20.18.0
```

## Automatic Version Management

The `.nvmrc` file in this project will automatically tell `nvm` which version to use when you enter the project directory.

## Troubleshooting

If you encounter engine compatibility warnings, ensure you are using the specified Node.js version.
