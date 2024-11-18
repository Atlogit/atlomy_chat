# Use an official Node runtime as a parent image
FROM node:20.18.0-alpine

# Set working directory
WORKDIR /app

# Install system dependencies for node-gyp and other compilation needs
RUN apk add --no-cache python3 make g++

# Install dependencies
# Copy package files first
COPY package*.json ./

# Debug: List and display package files
RUN ls -l && cat package.json && cat package-lock.json

# Install ALL dependencies (prod and dev) with node-gyp rebuild
RUN npm install -g npm@latest && \
    npm install --verbose && \
    npm rebuild

# Copy the rest of the application code
COPY . .

# Build the Next.js application with verbose output
RUN npm run build --verbose

# Expose the port the app runs on
EXPOSE 3000

# Set environment to production
ENV NODE_ENV=production

# Start the application
CMD ["npm", "run", "start"]
