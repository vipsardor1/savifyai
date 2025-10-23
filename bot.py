import telebot
import yt_dlp
import os

BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"
bot = telebot.TeleBot(BOT_TOKEN)

def download_media(url):
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'quiet': True
    }

    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    ydl_opts = {
    'format': 'bestvideo+bestaudio/best',
    'merge_output_format': 'mp4',
    'quiet': True,
    'extract_flat': False,
    'noplaylist': True,
    'nocheckcertificate': True,
    'geo_bypass': True,
}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return filename, info.get('title', 'unknown')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "🎧 Salom! Men video, rasm va musiqa yuklab beruvchi botman.\n\n"
        "📲 Menga shunchaki *YouTube, TikTok, Instagram, Spotify* yoki *Yandex Music* link yuboring."
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    if not any(x in url for x in ['youtube', 'tiktok', 'instagram', 'spotify', 'yandex']):
        bot.reply_to(message, "❌ Iltimos, to‘g‘ri link yuboring.")
        return

    msg = bot.reply_to(message, "⬇️ Yuklanmoqda, biroz kuting...")

    try:
        file_path, title = download_media(url)
        with open(file_path, 'rb') as f:
            if file_path.endswith(('.mp3', '.m4a', '.wav')):
                bot.send_audio(message.chat.id, f, title=title)
            elif file_path.endswith(('.mp4', '.mkv', '.mov')):
                bot.send_video(message.chat.id, f, caption=title)
            else:
                bot.send_document(message.chat.id, f)

        bot.delete_message(message.chat.id, msg.message_id)
        os.remove(file_path)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Xato yuz berdi: {e}")

bot.infinity_polling()
