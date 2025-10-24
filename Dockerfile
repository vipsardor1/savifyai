FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y git ffmpeg

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]

RUN apt-get update && apt-get install -y git ffmpeg
