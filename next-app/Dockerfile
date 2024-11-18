# Use an official Node runtime as a parent image
FROM node:20.18.0-alpine

# Set working directory
WORKDIR /app

# Install dependencies
# Copy package.json and package-lock.json
COPY package*.json ./

# Debug: List and display package files
RUN ls -l && cat package.json && cat package-lock.json

# Install dependencies with more verbose output
RUN npm install --verbose

# Copy the rest of the application code
COPY . .

# Build the Next.js application
RUN npm run build

# Expose the port the app runs on
EXPOSE 3000

# Set environment to production
ENV NODE_ENV=production

# Start the application
CMD ["npm", "run", "start"]
