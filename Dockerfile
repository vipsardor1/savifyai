FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
# (Other Dockerfile lines like FROM python:3.10)

# Install system packages required by our Python libraries
RUN apt-get update && apt-get install -y git ffmpeg

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# (Other lines like COPY . . and CMD ["python", "main.py"])
