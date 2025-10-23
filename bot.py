8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98
import os
import tempfile
from pathlib import Path
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext

from insta_downloader import download_reel, download_profile_posts  # reuse your functions

BOT_TOKEN = os.getenv("8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98")  # set your token in environment variable
if not BOT_TOKEN:
    raise RuntimeError("Please set BOT_TOKEN environment variable")

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "👋 Hi! Send me an Instagram link or username.\n"
        "I’ll download posts, reels, or stories for you."
    )

def handle_instagram(update: Update, context: CallbackContext):
    text = update.message.text.strip()

    update.message.reply_text("⏬ Downloading... Please wait.")
    tmp_dir = tempfile.mkdtemp()

    try:
        if "instagram.com" in text:
            # Link to reel/post
            download_reel(text)
        else:
            # Assume it's a username
            download_profile_posts(text, max_count=3)

        # Find downloaded files
        download_dir = Path("downloads") / text.strip("@").split("/")[-1]
        if not download_dir.exists():
            update.message.reply_text("❌ Nothing downloaded.")
            return

        for file in download_dir.glob("*"):
            if file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                update.message.reply_photo(photo=open(file, "rb"))
            elif file.suffix.lower() in [".mp4", ".mov"]:
                update.message.reply_video(video=open(file, "rb"))

        update.message.reply_text("✅ Done!")

    except Exception as e:
        update.message.reply_text(f"⚠️ Error: {e}")
        print(e)

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_instagram))
    updater.start_polling()
    print("🤖 Bot is running...")
    updater.idle()

if __name__ == "__main__":
    main()

