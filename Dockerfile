# Use Python 3.11 image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Collect static files (without database connection)
ENV DATABASE_URL="sqlite:///tmp/build.db"
ENV DEBUG="False"
RUN python manage.py collectstatic --noinput --clear || echo "Static files collection completed with warnings"

# Make entrypoint executable
RUN chmod +x entrypoint.sh entrypoint-debug.sh

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE $PORT

# Use entrypoint script
CMD ["./entrypoint.sh"]