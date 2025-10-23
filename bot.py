import os

# vaqtinchalik papka yaratish
if not os.path.exists("/tmp/insta"):
    os.makedirs("/tmp/insta")

import telebot
import yt_dlp
import os
import tempfile
from shazamio import Shazam
from spotdl import Spotdl
import asyncio
import instaloader
from pydub import AudioSegment
import subprocess

# === CONFIG ===
BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"  # 👈 shu joyga o'zingning tokeningni qo'y
bot = telebot.TeleBot(BOT_TOKEN)

# === Helper: download video ===
def download_media(url):
    tempdir = tempfile.mkdtemp()
    ydl_opts = {
        "outtmpl": f"{tempdir}/%(title)s.%(ext)s",
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return filename

# === Instagram photo downloader ===
def download_instagram_photo(url):
    loader = instaloader.Instaloader(dirname_pattern=tempfile.gettempdir(), save_metadata=False)
    loader.download_post(instaloader.Post.from_shortcode(loader.context, url.split("/")[-2]), target="insta")
    folder = os.path.join(tempfile.gettempdir(), "insta")
    for file in os.listdir(folder):
        if file.endswith(".jpg") or file.endswith(".png"):
            return os.path.join(folder, file)
    return None

# === Extract audio & recognize music ===
async def recognize_music(file_path):
    audio_path = file_path.replace(".mp4", ".mp3")
    AudioSegment.from_file(file_path).export(audio_path, format="mp3")
    shazam = Shazam()
    out = await shazam.recognize_song(audio_path)
    if "track" in out:
        track = out["track"]
        return f"🎶 {track['title']} - {track['subtitle']}\n🔗 {track['share']['href']}"
    else:
        return "❌ Musiqa aniqlanmadi."

# === Spotify downloader ===
def download_spotify(link):
    subprocess.run(["spotdl", link, "--output", tempfile.gettempdir()], check=False)
    for file in os.listdir(tempfile.gettempdir()):
        if file.endswith(".mp3"):
            return os.path.join(tempfile.gettempdir(), file)
    return None

# === Command: /start ===
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "👋 Salom! Men YouTube, Instagram, TikTok, Spotify, va Shazam botman.\nLink yuboring 🎥🎵")

# === Process links ===
@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    url = message.text.strip()
    bot.send_chat_action(message.chat.id, "upload_video")

    try:
        if "instagram.com" in url and "/p/" in url:
            photo = download_instagram_photo(url)
            bot.send_photo(message.chat.id, open(photo, "rb"), caption="📸 Instagram rasm")
        elif any(x in url for x in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com/reel"]):
            video = download_media(url)
            bot.send_video(message.chat.id, open(video, "rb"), caption="🎬 Yuklab olindi (Full HD)")
        elif "spotify.com" in url:
            mp3 = download_spotify(url)
            bot.send_audio(message.chat.id, open(mp3, "rb"), caption="🎵 Spotify qo'shiq")
        else:
            bot.reply_to(message, "❌ Noto‘g‘ri link. YouTube, TikTok, Instagram, Spotify yoki Yandex link yuboring.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Xato: {e}")

# === Command: /shazam ===
@bot.message_handler(commands=["shazam"])
def shazam_start(message):
    bot.reply_to(message, "🎤 Musiqa faylini yuboring (audio yoki video) — men nomini topaman.")

@bot.message_handler(content_types=["audio", "video", "voice"])
def handle_audio(message):
    try:
        file_info = bot.get_file(message.audio.file_id if message.content_type == "audio" else message.video.file_id)
        file = bot.download_file(file_info.file_path)
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(file)
        temp.close()

        bot.reply_to(message, "🔍 Musiqa aniqlanmoqda...")
        result = asyncio.run(recognize_music(temp.name))
        bot.send_message(message.chat.id, result)
        os.remove(temp.name)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Xato: {e}")

print("✅ Bot ishga tushdi...")
bot.infinity_polling()
