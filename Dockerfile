# Build the frontend 
FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Install backend dependencies
FROM node:22-alpine AS backend-deps

WORKDIR /backend
COPY backend/package.json backend/package-lock.json ./
RUN npm ci --omit=dev

# Final all-in-one image
FROM python:3.13-slim

# Install core system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    nginx \
    supervisor \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 22 via nodesource
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python agents
COPY agents/requirements.txt /app/agents/requirements.txt
RUN pip install --no-cache-dir -r /app/agents/requirements.txt

COPY agents/main.py agents/pipeline.py /app/agents/
COPY agents/agents/ /app/agents/agents/

# Node.js backend 
COPY --from=backend-deps /backend/node_modules /app/backend/node_modules
COPY backend/package.json /app/backend/
COPY backend/server.js /app/backend/
COPY backend/config /app/backend/config
COPY backend/controllers /app/backend/controllers
COPY backend/middleware /app/backend/middleware
COPY backend/models /app/backend/models
COPY backend/routes /app/backend/routes

# Frontend static files → nginx 
COPY --from=frontend-build /frontend/dist /var/www/html

# Configuration files 
COPY deploy/nginx.conf /etc/nginx/sites-enabled/default
COPY deploy/supervisord.conf /etc/supervisor/conf.d/invoxio.conf

# Expose single port nginx handles routing
EXPOSE 3000

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/invoxio.conf"]

