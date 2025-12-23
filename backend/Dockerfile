# Change this line:
# FROM python:3.9-slim
# To this:
FROM python:3.10.11

# The rest of your Dockerfile is perfect and does not need to change.
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]