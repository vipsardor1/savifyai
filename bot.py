import os
import instaloader
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98" # tokeningizni shu yerga yozing

# /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Men Instaloader botman.\n"
        "📸 Menga Instagram post yoki reel link yuboring — men uni yuklab beraman!"
    )

# Yuklab olish funksiyasi
async def download_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "instagram.com" not in url:
        await update.message.reply_text("❌ Iltimos, to‘g‘ri Instagram link yuboring!")
        return

    await update.message.reply_text("⏳ Yuklanmoqda... biroz kuting.")

    try:
        loader = instaloader.Instaloader(dirname_pattern="downloads", save_metadata=False)
        shortcode = url.split("/")[-2]  # masalan: https://www.instagram.com/reel/XXXX/ → 'XXXX'

        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        file_path = f"downloads/{shortcode}"

        if post.is_video:
            loader.download_post(post, target=file_path)
            video_file = None
            # yuklangan faylni topish
            for file in os.listdir(file_path):
                if file.endswith(".mp4"):
                    video_file = os.path.join(file_path, file)
                    break
            if video_file:
                await update.message.reply_video(video=open(video_file, "rb"), caption="🎬 Video yuklandi!")
            else:
                await update.message.reply_text("⚠️ Video topilmadi.")
        else:
            loader.download_post(post, target=file_path)
            image_file = None
            for file in os.listdir(file_path):
                if file.endswith(".jpg"):
                    image_file = os.path.join(file_path, file)
                    break
            if image_file:
                await update.message.reply_photo(photo=open(image_file, "rb"), caption="🖼 Rasm yuklandi!")
            else:
                await update.message.reply_text("⚠️ Rasm topilmadi.")

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
