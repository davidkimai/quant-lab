FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY packages/web/package*.json ./

# Install dependencies
# Use npm ci if package-lock.json exists, otherwise npm install
RUN if [ -f package-lock.json ]; then \
      echo "Using npm ci (package-lock.json found)"; \
      npm ci; \
    else \
      echo "Using npm install (no package-lock.json)"; \
      npm install; \
    fi

# Copy source files
COPY packages/web/ ./

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Run development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
