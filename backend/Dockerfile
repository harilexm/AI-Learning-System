# backend/Dockerfile

# --- THIS IS THE FIX ---
# Use the 'bullseye' version, which is a more modern and stable base than 'buster'
FROM python:3.10-bullseye

# Install system-level dependencies. This process is more reliable on bullseye.
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]