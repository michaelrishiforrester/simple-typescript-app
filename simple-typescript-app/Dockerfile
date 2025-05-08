# Builder stage
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Security scan
RUN npm audit --production

# Production stage
FROM node:20-alpine AS production

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Set working directory
WORKDIR /usr/src/app

# Copy only production dependencies from builder stage
COPY --from=builder /usr/src/app/package*.json ./
RUN npm ci --only=production

# Copy built app from builder stage
COPY --from=builder /usr/src/app/dist ./dist

# Set ownership to non-root user
RUN chown -R appuser:appgroup /usr/src/app

# Switch to non-root user
USER appuser

# Environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Expose port
EXPOSE 3000

# Start the app
CMD ["node", "dist/app.js"]