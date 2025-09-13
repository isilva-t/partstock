FROM python:3.12-slim

# Build arguments for user configuration
ARG USER_ID=0
ARG GROUP_ID=0

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
	sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create user only if not root (for development)
RUN if [ ${USER_ID} -ne 0 ]; then \
    groupadd -g ${GROUP_ID} appuser && \
    useradd -u ${USER_ID} -g ${GROUP_ID} -m appuser && \
    chown -R appuser:appuser /app; \
    fi

# Expose port
EXPOSE 8000

# Switch to created user (or stay root if USER_ID=0)
USER ${USER_ID}:${GROUP_ID}

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
