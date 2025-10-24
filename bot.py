import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 🔹 Agar Railway-da bo‘lsangiz, Environment Variables-da BOT_TOKEN kiriting.
# Agar lokalda sinov qilayotgan bo‘lsangiz, quyidagidek yozing:
BOT_TOKEN =  "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"  # Tokeningizni shu yerga yozing

# /start buyrug‘i
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Men SaveGram botman.\n"
        "Menga Instagram post, reel yoki story link yuboring — men uni yuklab beraman 📥"
    )

# Instagram linkni qabul qilib, yuklash
async def download_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text.strip()

    if "instagram.com" not in link:
        await update.message.reply_text("❌ Iltimos, to‘g‘ri Instagram link yuboring!")
        return

    await update.message.reply_text("⏳ Yuklanmoqda, biroz kuting...")

    try:
        # SaveGram API dan ma’lumot olish
        response = requests.get(f"https://savegram.io/api?url={link}")
        print("🔍 Server javobi:", response.text)  # debug uchun

        data = response.json()

        # Tekshirish
        if "medias" in data and len(data["medias"]) > 0:
            media_url = data["medias"][0]["url"]

            # Foydalanuvchiga video/rasm yuborish
            if data["medias"][0]["type"] == "video":
                await update.message.reply_video(video=media_url, caption="🎬 Video yuklandi!")
            else:
                await update.message.reply_photo(photo=media_url, caption="🖼 Rasm yuklandi!")
        else:
            await update.message.reply_text("⚠️ Hech narsa topilmadi. Linkni qayta tekshirib yuboring.")

    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")

# Asosiy ishga tushirish funksiyasi
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_instagram))

    print("🚀 Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
