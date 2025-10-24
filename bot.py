 "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"

# Download command
async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /post <instagram_url>")
        return

    url = context.args[0]
    await update.message.reply_text("⏳ Downloading... please wait")

    try:
        api_url = "https://snapsave.app/action.php?lang=en"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest"
        }
        data = {"url": url}

        response = requests.post(api_url, headers=headers, data=data)
        if response.status_code != 200:
            await update.message.reply_text("❌ API connection failed.")
            return

        html = response.text
        # Extract download links manually
        links = []
        import re
        matches = re.findall(r'href="(https://[^"]+\.mp4[^"]*)"', html)
        links.extend(matches)

        if not links:
            await update.message.reply_text("❌ Could not find downloadable media.")
            return

        for link in links:
            await update.message.reply_text("🎥 Sending video...")
            await update.message.reply_video(video=link)
        await update.message.reply_text("✅ Done!")

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
        print("Error:", e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send me an Instagram link using:\n\n"
        "/post <url>\n\nExample:\n/post https://www.instagram.com/reel/DPpyKvsAi5J/"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post))
    print("🚀 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
