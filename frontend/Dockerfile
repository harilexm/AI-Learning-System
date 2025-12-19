# frontend/Dockerfile

# --- Stage 1: The Build Stage ---
# Use an official Node.js image as the builder.
# 'alpine' is a lightweight version.
# frontend/Dockerfile

FROM node:20-alpine AS builder

# Set the working directory in the container
WORKDIR /app

# Copy the package.json and package-lock.json files
COPY package*.json ./

# Install all dependencies
RUN npm install
# Copy the rest of the application's source code
COPY . .

# Run the build command to compile the Vue app

# This creates a 'dist' folder with our static files
RUN npm run build

# --- Stage 2: The Serve Stage ---
# Start from a fresh, lightweight Nginx image
FROM nginx:1.23-alpine

# Copy the compiled static files from the 'builder' stage
# into the Nginx web server's public directory
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our custom Nginx configuration file
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 to the outside world
EXPOSE 80

# The default Nginx command will start the server automatically
# CMD ["nginx", "-g", "daemon off;"] is implicitly run