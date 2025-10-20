# Dockerfile: frontend (Vite/npm based)

# 1. Build Stage: Node-alpine for light build environment
FROM node:22-alpine as builder
WORKDIR /app

# Copy package files and install dependencies
COPY frontend/package.json ./package.json
COPY frontend/package-lock.json ./package-lock.json 

RUN npm install

# Copy source code and run the build command for Vite
COPY frontend/. .
RUN npm run build # Vite build command

# 2. Run Stage: Use NGINX for serving static files (Best Practice)
FROM nginx:alpine
# Copy the built files from the builder stage into Nginx's HTML directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy a custom Nginx configuration to handle React routing (optional, but good practice)
# COPY nginx.conf /etc/nginx/conf.d/default.conf 

EXPOSE 80 
# Note: In docker-compose.yml we map 3000:80

CMD ["nginx", "-g", "daemon off;"]