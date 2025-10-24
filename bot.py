 "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"
import os
import instaloader
import requests
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"  # set this in Railway or locally

L = instaloader.Instaloader()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me an Instagram post link!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "instagram.com" not in url:
        await update.message.reply_text("Please send a valid Instagram link.")
        return

    try:
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        if post.is_video:
            file_url = post.video_url
        else:
            file_url = post.url

        response = requests.get(file_url)
        if response.status_code == 200:
            bio = BytesIO(response.content)
            bio.name = "insta_media.jpg" if not post.is_video else "insta_video.mp4"
            await update.message.reply_document(bio)
        else:
            await update.message.reply_text("Could not fetch media.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
