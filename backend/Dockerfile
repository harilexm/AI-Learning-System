FROM python:3.10-slim

# Set working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port that Gunicorn will run on
EXPOSE 5000

# Define the command to run your application
# gunicorn will run the 'app' object inside your 'app.py' file
# We bind it to 0.0.0.0 so it can be accessed from outside the container
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]