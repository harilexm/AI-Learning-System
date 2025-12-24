FROM python:3.10.11

WORKDIR /app

# Copy the requirements file from the backend subfolder and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code from the backend subfolder
COPY backend/ .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]