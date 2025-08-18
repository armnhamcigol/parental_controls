# Dockerfile for Parental Controls Dashboard on Raspberry Pi
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    openssh-client \
    curl \
    && rm -rf /var/cache/apk/*

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy application source
COPY src/ ./src/
COPY *.md ./

# Create necessary directories
RUN mkdir -p config logs && \
    chown -R node:node /app

# Switch to non-root user
USER node

# Expose port 3000
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Start the application
CMD ["node", "src/controller.js"]
