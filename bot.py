import os
import instaloader
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 🔹 Tokeningizni shu yerga yozing
BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"

# 🔹 Instagram login ma’lumotlaringizni yozing
IG_USERNAME = "savifyai"
IG_PASSWORD = "200502saxx"

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Menga Instagram post yoki reel link yuboring — men uni yuklab beraman!"
    )

# Yuklab olish funksiyasi
async def download_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "instagram.com" not in url:
        await update.message.reply_text("❌ Iltimos, to‘g‘ri Instagram link yuboring!")
        return

    await update.message.reply_text("⏳ Yuklanmoqda... biroz kuting.")

    try:
        os.makedirs("downloads", exist_ok=True)

        loader = instaloader.Instaloader(dirname_pattern="downloads", save_metadata=False)
        loader.login(IG_USERNAME, IG_PASSWORD)  # 🔐 Instagram login

        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(loader.context, shortcode)

        target_folder = os.path.join("downloads", shortcode)
        os.makedirs(target_folder, exist_ok=True)

        loader.download_post(post, target=target_folder)

        # Fayllarni tekshirish
        media_files = [os.path.join(target_folder, f) for f in os.listdir(target_folder)]
        image_files = [f for f in media_files if f.endswith(".jpg")]
        video_files = [f for f in media_files if f.endswith(".mp4")]

        if video_files:
            await update.message.reply_video(video=open(video_files[0], "rb"), caption="🎬 Video yuklandi!")
        elif image_files:
            await update.message.reply_photo(photo=open(image_files[0], "rb"), caption="🖼 Rasm yuklandi!")
        else:
            await update.message.reply_text("⚠️ Fayl topilmadi, lekin bu post private yoki story bo‘lishi mumkin.")

    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")

# Botni ishga tushirish
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_instagram))
    print("🚀 Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
