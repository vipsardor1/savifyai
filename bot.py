import os
import uuid
import logging
import telebot
import yt_dlp
import instaloader

# Enable logging for debugging
logging.basicConfig(level=logging.INFO)

# Initialize bot with your token
bot = telebot.TeleBot("8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98")

# Temporary media directory
TMP = "/tmp/media"
os.makedirs(TMP, exist_ok=True)

# Utility to generate unique file paths
def get_temp_path(prefix, ext="mp4"):
    return os.path.join(TMP, f"{prefix}_{uuid.uuid4().hex}.{ext}")

# Start command handler
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "🎧 Yuboring: YouTube, TikTok, Instagram, Spotify, yoki Yandex Music link.")

# Main message handler
@bot.message_handler(func=lambda m: True)
def handle_message(msg):
    text = msg.text.strip()
    if "youtube.com" in text or "youtu.be" in text:
        download_youtube(msg, text)
    elif "tiktok.com" in text:
        download_tiktok(msg, text)
    elif "instagram.com" in text:
        download_instagram(msg, text)
    else:
        bot.reply_to(msg, "❌ Noma'lum link — faqat YouTube, TikTok, yoki Instagram.")

# YouTube downloader
def download_youtube(msg, url):
    bot.send_message(msg.chat.id, "📹 YouTube video yuklanmoqda...")
    path = get_temp_path("yt")
    ydl_opts = {
        "outtmpl": path,
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4"
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        with open(path, "rb") as v:
            bot.send_video(msg.chat.id, v)
        os.remove(path)
    except Exception as e:
        bot.send_message(msg.chat.id, f"⚠️ Xato: {e}")

# TikTok downloader
def download_tiktok(msg, url):
    bot.send_message(msg.chat.id, "🎬 TikTok video yuklanmoqda...")
    path = get_temp_path("tt")
    ydl_opts = {
        "outtmpl": path,
        "format": "best",
        "merge_output_format": "mp4"
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        with open(path, "rb") as v:
            bot.send_video(msg.chat.id, v)
        os.remove(path)
    except Exception as e:
        bot.send_message(msg.chat.id, f"⚠️ Xato: {e}")

# Instagram downloader
def download_instagram(msg, url):
    bot.send_message(msg.chat.id, "📸 Instagramdan yuklanmoqda...")
    try:
        shortcode = [part for part in url.split("/") if part][-1]
        target_folder = os.path.join(TMP, f"insta_{uuid.uuid4().hex}")
        os.makedirs(target_folder, exist_ok=True)
        L = instaloader.Instaloader(dirname_pattern=target_folder)
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=target_folder)
        for file in os.listdir(target_folder):
            fpath = os.path.join(target_folder, file)
            if file.endswith(('.jpg', '.jpeg', '.png')):
                with open(fpath, "rb") as i:
                    bot.send_photo(msg.chat.id, i)
            elif file.endswith(".mp4"):
                with open(fpath, "rb") as v:
                    bot.send_video(msg.chat.id, v)
            os.remove(fpath)
        os.rmdir(target_folder)
    except Exception as e:
        bot.send_message(msg.chat.id, f"⚠️ Xato: {e}")

# Start polling
bot.polling()
