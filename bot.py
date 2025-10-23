"8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"  # For testing only
import instaloader
from pathlib import Path

def get_loader():
    L = instaloader.Instaloader(
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        post_metadata_txt_pattern=""
    )
    L.load_session_from_file("savifyai")  # o‘z username’ingizni yozing
    return L

def download_reel(url: str, target_dir="downloads"):
    L = get_loader()
    shortcode = url.strip("/").split("/")[-1]
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    L.download_post(post, target=Path(target_dir) / "reel")

def download_profile_posts(username: str, max_count=3, target_dir="downloads"):
    L = get_loader()
    profile = instaloader.Profile.from_username(L.context, username.strip("@"))
    for idx, post in enumerate(profile.get_posts()):
        if idx >= max_count:
            break
        L.download_post(post, target=Path(target_dir) / username.strip("@"))
import os
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"); 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Menga Instagram link yoki username yuboring.\n"
        "Men sizga post, reel yoki story’larni yuklab beraman (HD sifatida)."
    )

async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    await update.message.reply_text("⏬ Yuklanmoqda... kuting.")

    try:
        if "instagram.com" in text:
            download_reel(text)
            target_name = "reel"
        else:
            download_profile_posts(text, max_count=3)
            target_name = text.strip("@")

        download_dir = Path("downloads") / target_name
        if not download_dir.exists():
            await update.message.reply_text("❌ Hech narsa topilmadi.")
            return

        for file in download_dir.glob("*"):
            with open(file, "rb") as f:
                await update.message.reply_document(document=f)

        await update.message.reply_text("✅ Tayyor! Fayllar original sifatida yuborildi.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Xato: {e}")
        print(e)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_instagram))
    print("🤖 Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()

