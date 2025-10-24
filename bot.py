import os
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98" # o‘zingizning tokeningizni yozing

# /start buyrug‘i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Men SnapInsta botman.\n"
        "Menga Instagram post yoki reel link yuboring — men uni yuklab beraman 📥"
    )

# Yuklab olish funksiyasi
async def download_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()

    if "instagram.com" not in link:
        await update.message.reply_text("❌ Iltimos, to‘g‘ri Instagram link yuboring!")
        return

    await update.message.reply_text("⏳ Yuklanmoqda, biroz kuting...")

    try:
        response = requests.get(f"https://snapinsta.app/api?url={link}", headers={
            "User-Agent": "Mozilla/5.0"
        })

        html = response.text
        print("🔍 HTML uzunligi:", len(html))  # tekshirish uchun

        # Video yoki rasm URL ni HTML ichidan ajratib olish
        urls = re.findall(r'(https?://[^"]+\.(?:mp4|jpg|jpeg|png))', html)

        if not urls:
            await update.message.reply_text("⚠️ Yuklab olinadigan fayl topilmadi.")
            return

        media_url = urls[0]

        if media_url.endswith(".mp4"):
            await update.message.reply_video(video=media_url, caption="🎬 Video yuklandi!")
        else:
            await update.message.reply_photo(photo=media_url, caption="🖼 Rasm yuklandi!")

    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")

# Asosiy ishga tushirish
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_instagram))
    print("🚀 Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
