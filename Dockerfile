FROM python:3.12-slim

# Install system dependencies required for building packages
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /setup

# Upgrade pip first
RUN pip install --upgrade pip

# Copy requirements.txt and install dependencies
COPY requirements.txt /setup/
RUN pip install -r requirements.txt

# Install additional packages
RUN pip install psycopg2-binary
RUN pip install drf-yasg

# Install gunicorn
RUN pip install gunicorn

# Copy the project files
COPY . /setup/

# Command to run when the container starts
CMD ["gunicorn", "setup.wsgi:application", "--bind", "0.0.0.0:8000"]