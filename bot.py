import os
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from insta_downloader import download_reel, download_profile_posts

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"  # For testing

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send me an Instagram link or username.\n"
        "I’ll download posts, reels, or stories for you."
    )

async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    await update.message.reply_text("⏬ Downloading... Please wait.")

    try:
        if "instagram.com" in text:
            download_reel(text)
        else:
            download_profile_posts(text, max_count=3)

        download_dir = Path("downloads") / text.strip("@").split("/")[-1]
        if not download_dir.exists():
            await update.message.reply_text("❌ Nothing downloaded.")
            return

        for file in download_dir.glob("*"):
            if file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                with open(file, "rb") as f:
                    await update.message.reply_photo(photo=f)
            elif file.suffix.lower() in [".mp4", ".mov"]:
                with open(file, "rb") as f:
                    await update.message.reply_video(video=f)

        await update.message.reply_text("✅ Done!")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")
        print(e)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_instagram))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
