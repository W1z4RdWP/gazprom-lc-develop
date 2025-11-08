# Dockerfile

# Use the official Python image from Docker Hub as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Environment variables to prevent Python from writing .pyc files and to buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1



# Copy the requirements.txt file into the container
COPY ./requirements.txt .

# Install the Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Создаем директорию для логов и даем права
RUN mkdir -p /var/log/django && chown -R www-data:www-data /var/log/django

# Collect static files for the Django application
RUN python manage.py collectstatic --noinput

# Открыть порт 8000 на входящий к приложению трафик
EXPOSE 8000

# Define the command to run the application
CMD ["gunicorn", "myproject.wsgi:application", "--bind", "0.0.0.0:8000"]
