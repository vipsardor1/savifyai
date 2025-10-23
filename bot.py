"8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"  # For testing only
import os
import re
from pathlib import Path
import instaloader
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- Config ---
BOT_TOKEN = os.getenv("8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98") or "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"
IG_SESSION_USER = os.getenv("savifyai") or "savifyai"  # sessiya yaratgan username

DOWNLOAD_ROOT = Path("downloads")
DOWNLOAD_ROOT.mkdir(exist_ok=True)

# --- Instaloader helper ---
def get_loader():
    L = instaloader.Instaloader(
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        post_metadata_txt_pattern=""
    )
    # Sessiya faylini yuklash
    L.load_session_from_file(IG_SESSION_USER)
    return L

def extract_shortcode(url: str):
    url = url.strip()
    patterns = [
        r"instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)/?",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None

# --- Downloaders ---
def download_reel_or_post(url: str, target_dir: Path):
    L = get_loader()
    shortcode = extract_shortcode(url)
    if not shortcode:
        raise ValueError("Link noto‘g‘ri. To‘liq Instagram link yuboring.")
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    target_dir.mkdir(parents=True, exist_ok=True)
    L.download_post(post, target=target_dir)

def download_profile_posts(username: str, max_count=3, target_dir: Path = DOWNLOAD_ROOT):
    L = get_loader()
    username = username.strip().lstrip("@")
    profile = instaloader.Profile.from_username(L.context, username)
    target_dir = target_dir / username
    target_dir.mkdir(parents=True, exist_ok=True)
    for idx, post in enumerate(profile.get_posts()):
        if idx >= max_count:
            break
        L.download_post(post, target=target_dir)
    return target_dir

# --- Telegram Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Menga Instagram link yoki username yuboring.\n"
        "Men sizga post yoki reel’larni HD sifatida yuklab beraman."
    )

async def handle_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    await update.message.reply_text("⏬ Yuklanmoqda... kuting.")

    try:
        if "instagram.com" in text:
            target_dir = DOWNLOAD_ROOT / "reel_or_post"
            download_reel_or_post(text, target_dir)
        else:
            target_dir = download_profile_posts(text, max_count=3)

        if not target_dir.exists():
            await update.message.reply_text("❌ Hech narsa yuklanmadi.")
            return

        files = sorted(target_dir.glob("*"))
        if not files:
            await update.message.reply_text("❌ Fayl topilmadi.")
            return

        for file in files:
            if file.is_file():
                with open(file, "rb") as f:
                    await update.message.reply_document(document=f)

        await update.message.reply_text("✅ Tayyor! Fayllar original sifatida yuborildi.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Xato: {e}")
        print(e)

# --- Main ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_instagram))
    print("🤖 Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
