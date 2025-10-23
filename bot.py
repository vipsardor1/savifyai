import telebot
import os
import subprocess
import yt_dlp

BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"

bot = telebot.TeleBot(BOT_TOKEN)

# Yuklab olish funksiyasi
def download_instagram_media(url):
    ydl_opts = {
        "outtmpl": "insta/%(id)s.%(ext)s",
        "format": "bestvideo+bestaudio/best",
        "quiet": True,
    }
    os.makedirs("insta", exist_ok=True)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename

@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id, "📸 Menga Instagram video, rasm yoki story linkini yubor!")

@bot.message_handler(func=lambda m: True)
def handle_message(msg):
    url = msg.text.strip()

    if "instagram.com" not in url:
        bot.send_message(msg.chat.id, "❌ Iltimos, faqat Instagram link yuboring.")
        return

    bot.send_message(msg.chat.id, "⏳ Yuklanmoqda...")

    try:
        file_path = download_instagram_media(url)
        if file_path.endswith(".jpg") or file_path.endswith(".jpeg") or file_path.endswith(".png"):
            with open(file_path, "rb") as f:
                bot.send_photo(msg.chat.id, f)
        else:
            with open(file_path, "rb") as f:
                bot.send_video(msg.chat.id, f)
        bot.send_message(msg.chat.id, "✅ Yuklandi!")
        os.remove(file_path)
    except Exception as e:
        bot.send_message(msg.chat.id, f"⚠️ Xato: {e}")

print("🤖 Bot ishga tushdi...")
bot.polling()

