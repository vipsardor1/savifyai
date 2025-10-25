# Use lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file first
COPY requirements.txt .

# Install system dependencies (git and ffmpeg)
# git: required by requirements.txt to install acrcloud_sdk
# ffmpeg: required by ffmpeg-python to extract audio
RUN apt-get update && apt-get install -y git ffmpeg

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code (assuming you renamed bot.py to saveasbot.py)
COPY saveasbot.py .

# Run the bot
# Railway will inject your API_ID, API_HASH, BOT_TOKEN, etc.
# as environment variables
CMD ["python", "saveasbot.py"]
