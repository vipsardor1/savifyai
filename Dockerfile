# 1️⃣ Python bazasi
FROM python:3.10-slim

# 2️⃣ ffmpeg o‘rnatish
RUN apt-get update && apt-get install -y ffmpeg

# 3️⃣ Ishchi papka
WORKDIR /app

# 4️⃣ Fayllarni nusxalash
COPY . .

# 5️⃣ Kutubxonalarni o‘rnatish
RUN pip install --no-cache-dir -r requirements.txt

# 6️⃣ Asosiy faylni ishga tushurish
CMD ["python", "bot.py"]
