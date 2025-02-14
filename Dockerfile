FROM python:3

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /setup

# Copy requirements.txt and install dependencies
COPY requirements.txt /setup/

RUN pip install --upgrade setuptools wheel

RUN pip install -r requirements.txt

RUN pip install --upgrade pip

RUN pip install psycopg2-binary
RUN pip install drf-yasg



# Install gunicorn
RUN pip install gunicorn


# Copy the project files
COPY . /setup/


# Command to run when the container starts
CMD ["gunicorn", "setup.wsgi:application", "--bind", "0.0.0.0:8000"]