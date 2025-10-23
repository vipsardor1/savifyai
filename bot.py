import os
import telebot
import yt_dlp
import instaloader
from shazamio import Shazam

bot = telebot.TeleBot("8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98")

TMP = "/tmp/media"
os.makedirs(TMP, exist_ok=True)

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "🎧 Yuboring: YouTube, TikTok, Instagram, Spotify, yoki Yandex Music link.")

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

def download_youtube(msg, url):
    bot.send_message(msg.chat.id, "📹 YouTube video yuklanmoqda...")
    path = os.path.join(TMP, "yt.mp4")
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

def download_tiktok(msg, url):
    bot.send_message(msg.chat.id, "🎬 TikTok video yuklanmoqda...")
    path = os.path.join(TMP, "tt.mp4")
    ydl_opts = {"outtmpl": path, "format": "best", "merge_output_format": "mp4"}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        with open(path, "rb") as v:
            bot.send_video(msg.chat.id, v)
        os.remove(path)
    except Exception as e:
        bot.send_message(msg.chat.id, f"⚠️ Xato: {e}")

def download_instagram(msg, url):
    bot.send_message(msg.chat.id, "📸 Instagramdan yuklanmoqda...")
    try:
        L = instaloader.Instaloader(dirname_pattern=TMP)
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=TMP)
        files = [os.path.join(TMP, f) for f in os.listdir(TMP)]
        for file in files:
            if file.endswith(('.jpg', '.jpeg', '.png')):
                with open(file, "rb") as i: bot.send_photo(msg.chat.id, i)
            elif file.endswith(".mp4"):
                with open(file, "rb") as v: bot.send_video(msg.chat.id, v)
            os.remove(file)
    except Exception as e:
        bot.send_message(msg.chat.id, f"⚠️ Xato: {e}")

bot.polling()
