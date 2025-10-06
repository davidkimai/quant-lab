FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY packages/web/package.json packages/web/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source files
COPY packages/web/ ./

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Run development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
