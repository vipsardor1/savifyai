import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

load_dotenv()  # <-- bu .env faylni o‘qiydi
BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Menga Instagram link yuboring 👇")

async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    await update.message.reply_text("⏳ Yuklanmoqda...")

    try:
        # SaveGram API orqali yuklash
        api_url = f"https://savegram.app/api/download?url={url}"
        response = requests.get(f"https://savegram.io/api?url={link}")
print(response.text)  # nima javob qaytaryapti ko‘ring

        media = response.get("media", [])
        if not media:
            await update.message.reply_text("⚠️ Yuklab bo‘lmadi. Linkni tekshirib qayta urinib ko‘ring.")
            return

        first_media = media[0]
        media_url = first_media.get("url")

        if ".mp4" in media_url:
            await update.message.reply_video(media_url)
        else:
            await update.message.reply_photo(media_url)

    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram))

if __name__ == "__main__":
    app.run_polling()
