import os
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import instaloader

# --- Bot Token ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"  # For testing only

# --- Downloader Functions ---
def download_reel(url: str, target_dir="downloads"):
    """Download a single reel/post from Instagram in best quality."""
    L = instaloader.Instaloader(
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        post_metadata_txt_pattern=""
    )
    shortcode = url.strip("/").split("/")[-1]  # extract shortcode
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    L.download_post(post, target=Path(target_dir) / "reel")


def download_profile_posts(username: str, max_count=3, target_dir="downloads"):
    """Download latest posts from a profile in best quality."""
    L = instaloader.Instaloader(
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        post_metadata_txt_pattern=""
    )
    profile = instaloader.Profile.from_username(L.context, username.strip("@"))
    for idx, post in enumerate(profile.get_posts()):
        if idx >= max_count:
            break
        L.download_post(post, target=Path(target_dir) / username.strip("@"))

# --- Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send me an Instagram link or username.\n"
        "I’ll download posts, reels, or stories for you in the best quality."
    )

async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    await update.message.reply_text("⏬ Downloading in best quality... Please wait.")

    try:
        if "instagram.com" in text:
            download_reel(text)
            target_name = "reel"
        else:
            download_profile_posts(text, max_count=3)
            target_name = text.strip("@")

        download_dir = Path("downloads") / target_name
        if not download_dir.exists():
            await update.message.reply_text("❌ Nothing downloaded.")
            return

        for file in download_dir.glob("*"):
            suffix = file.suffix.lower()
            with open(file, "rb") as f:
                # Send as document to preserve full resolution
                await update.message.reply_document(document=f)

        await update.message.reply_text("✅ Done! Sent in original quality.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")
        print(e)

# --- Main ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_instagram))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
