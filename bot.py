import os
import telebot
import yt_dlp
import instaloader
import tempfile
import asyncio
from shazamio import Shazam

BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"  # <-- o'zingni tokeningni yoz
bot = telebot.TeleBot(BOT_TOKEN)

TMP_DIR = tempfile.gettempdir()
os.makedirs(TMP_DIR, exist_ok=True)

# ========== 1️⃣ Instagram yuklash ==========
@bot.message_handler(func=lambda msg: "instagram.com" in msg.text)
def handle_instagram(msg):
    url = msg.text.strip()
    bot.send_message(msg.chat.id, "📸 Instagram post yuklanmoqda...")

    try:
        loader = instaloader.Instaloader(dirname_pattern=TMP_DIR)
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=TMP_DIR)

        files = [os.path.join(TMP_DIR, f) for f in os.listdir(TMP_DIR)]

        if not files:
            bot.send_message(msg.chat.id, "⚠️ Hech qanday fayl topilmadi.")
            return

        for f in files:
            if f.endswith((".jpg", ".jpeg", ".png")):
                with open(f, "rb") as img:
                    bot.send_photo(msg.chat.id, img)
            elif f.endswith(".mp4"):
                with open(f, "rb") as vid:
                    bot.send_video(msg.chat.id, vid)

        for f in files:
            os.remove(f)

    except Exception as e:
        bot.send_message(msg.chat.id, f"⚠️ Xato: {e}")

# ========== 2️⃣ TikTok & YouTube yuklash ==========
@bot.message_handler(func=lambda msg: "tiktok.com" in msg.text or "youtube.com" in msg.text or "youtu.be" in msg.text)
def handle_video(msg):
    url = msg.text.strip()
    bot.send_message(msg.chat.id, "🎬 Video yuklanmoqda...")

    temp_file = os.path.join(TMP_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        "outtmpl": temp_file,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            with open(filename, "rb") as vid:
                bot.send_video(msg.chat.id, vid, caption=info.get("title", ""))
            os.remove(filename)
    except Exception as e:
        bot.send_message(msg.chat.id, f"⚠️ Xato: {e}")

# ========== 3️⃣ Audio dan Shazam (musiqani aniqlash) ==========
@bot.message_handler(content_types=["audio", "voice", "video"])
def recognize_music(msg):
    bot.send_message(msg.chat.id, "🎧 Musiqa aniqlanmoqda...")

    file_info = bot.get_file(msg.audio.file_id if msg.content_type == "audio" else msg.voice.file_id if msg.content_type == "voice" else msg.video.file_id)
    file_path = file_info.file_path
    downloaded_file = bot.download_file(file_path)
    temp_audio = os.path.join(TMP_DIR, "sample.mp3")

    with open(temp_audio, "wb") as f:
        f.write(downloaded_file)

    async def detect():
        shazam = Shazam()
        out = await shazam.recognize_song(temp_audio)
        if "track" in out:
            track = out["track"]
            title = track.get("title", "Noma'lum")
            artist = track.get("subtitle", "")
            url = track.get("url", "")
            bot.send_message(msg.chat.id, f"🎵 Topildi:\n<b>{title}</b> — {artist}\n{url}", parse_mode="HTML")
        else:
            bot.send_message(msg.chat.id, "❌ Musiqa aniqlanmadi.")

    asyncio.run(detect())
    os.remove(temp_audio)

# ========== 4️⃣ Default javob ==========
@bot.message_handler(func=lambda msg: True)
def fallback(msg):
    bot.reply_to(msg, "🔗 Iltimos, YouTube / TikTok / Instagram link yuboring yoki musiqa faylini tashlang.")

print("✅ Bot ishlayapti...")
bot.polling()

