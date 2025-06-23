FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY .env* ./

# Create necessary directories
RUN mkdir -p logs

# Create non-root user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Expose webhook port
EXPOSE 8443

# Run the bot
CMD ["python", "src/bot/telegram_agent_google.py"]