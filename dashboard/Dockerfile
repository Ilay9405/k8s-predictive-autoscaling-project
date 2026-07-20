# This is the Dockerfile for the dashboard application. The inference server's dockerfile is in /inference/Dockerfile.

# Stage 1: Build the React Application
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . ./
RUN npm run build

# Stage 2: Serve the App using Nginx
FROM nginx:alpine
# Copy the compiled React files from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html
# Copy our custom Nginx reverse-proxy configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
