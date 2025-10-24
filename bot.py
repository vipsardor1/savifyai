 "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"
import os
import instaloader
import requests
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"

L = instaloader.Instaloader()

# Optional Instagram login
IG_USER = os.getenv("IG_USER")
IG_PASS = os.getenv("IG_PASS")
if IG_USER and IG_PASS:
    try:
        L.login(IG_USER, IG_PASS)
        print("✅ Logged in to Instagram")
    except Exception as e:
        print("⚠️ Login failed:", e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send me an Instagram link.\n\n"
        "Commands:\n"
        "/post <url> - download a single post or reel\n"
        "/profile <username> - download latest 3 posts\n"
        "/story <username> - download current stories"
    )

async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /post <instagram_url>")
        return

    url = context.args[0]
    print(f"📩 Got URL: {url}")

    try:
        shortcode = url.split("/")[-2]
        print(f"➡️ Shortcode: {shortcode}")

        post = instaloader.Post.from_shortcode(L.context, shortcode)
        print("✅ Post fetched successfully")

        file_url = post.video_url if post.is_video else post.url
        caption = post.caption if post.caption else "(no caption)"
        print("📦 Downloading media from:", file_url)

        r = requests.get(file_url)
        bio = BytesIO(r.content)
        bio.name = "media.mp4" if post.is_video else "media.jpg"

        await update.message.reply_text(f"📝 Caption:\n{caption[:500]}")
        await update.message.reply_document(bio)
        print("✅ Sent media successfully")

    except Exception as e:
        print("❌ Error in /post:", e)
        await update.message.reply_text(f"❌ Error: {e}")

def main():
    print("🚀 Bot starting...")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post))

    app.run_polling()
    print("✅ Bot running!")

if __name__ == "__main__":
    main()
