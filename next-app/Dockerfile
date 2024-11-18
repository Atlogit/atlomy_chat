# Use an official Node runtime as a parent image
FROM node:20.18.0-alpine

# Set working directory to the Next.js app directory
WORKDIR /app

# Install system dependencies for node-gyp and other compilation needs
RUN apk add --no-cache python3 make g++ curl

# Set npm configuration for detailed logging and performance
RUN npm config set loglevel verbose && \
    npm config set progress true && \
    npm config set audit false

# Copy package files first
COPY package*.json ./

# Debug: Display Node and npm versions, and npm configuration
RUN node --version && \
    npm --version && \
    npm config list

# Clear npm cache and install dependencies with maximum verbosity
RUN npm cache clean --force && \
    npm install -g npm@latest && \
    NODE_OPTIONS=--max_old_space_size=4096 npm install --verbose

# Copy the rest of the application code
COPY . .

# Debug: Comprehensive file and dependency diagnostics
RUN echo "Project Files:" && ls -la && \
    echo "Package.json contents:" && cat package.json && \
    echo "Installed Packages:" && npm list --depth=1

# Enhanced build process with multiple layers of error logging
RUN set -e && \
    (npm run build --verbose || \
    (echo "Build Failed. Detailed Logs:" && \
    cat /root/.npm/_logs/2024-*-debug-0.log && \
    cat /root/.npm/_logs/2024-*-0.log && \
    npm run build --verbose --debug && \
    exit 1))

# Prune development dependencies
RUN npm prune --production

# Expose the port the app runs on
EXPOSE 3000

# Set environment to production
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Start the application
CMD ["npm", "run", "start"]
