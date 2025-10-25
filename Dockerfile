# Use lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code
COPY saveasbot.py .

# Create temp_downloads directory (used by bot)
RUN mkdir -p /app/temp_downloads

# Environment variables (set at runtime or via docker-compose)
ENV API_ID=""
ENV API_HASH=""
ENV BOT_TOKEN=""

# Run the bot
CMD ["python", "saveasbot.py"]
