 "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"
import os
import instaloader
import requests
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"  # set in Railway
L = instaloader.Instaloader()

# Optional login for private profiles
IG_USER = os.getenv("IG_USER")
IG_PASS = os.getenv("IG_PASS")
if IG_USER and IG_PASS:
    try:
        L.login(IG_USER, IG_PASS)
        print("Logged in to Instagram")
    except Exception as e:
        print("Login failed:", e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I can fetch Instagram content.\n"
        "Commands:\n"
        "/post <url>\n/profile <username>\n/story <username>\n/hashtag <tag>"
    )

async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /post <instagram_url>")
        return
    url = context.args[0]
    try:
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        file_url = post.video_url if post.is_video else post.url
        r = requests.get(file_url)
        bio = BytesIO(r.content)
        bio.name = "media.mp4" if post.is_video else "media.jpg"
        await update.message.reply_document(bio)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /profile <username>")
        return
    username = context.args[0]
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        count = 0
        for post in profile.get_posts():
            if count >= 3:  # limit to 3 posts for demo
                break
            url = post.video_url if post.is_video else post.url
            r = requests.get(url)
            bio = BytesIO(r.content)
            bio.name = "media.mp4" if post.is_video else "media.jpg"
            await update.message.reply_document(bio)
            count += 1
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /story <username>")
        return
    username = context.args[0]
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        for story in L.get_stories(userids=[profile.userid]):
            for item in story.get_items():
                url = item.video_url if item.is_video else item.url
                r = requests.get(url)
                bio = BytesIO(r.content)
                bio.name = "story.mp4" if item.is_video else "story.jpg"
                await update.message.reply_document(bio)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def hashtag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /hashtag <tag>")
        return
    tag = context.args[0]
    try:
        for post in instaloader.Hashtag.from_name(L.context, tag).get_posts():
            url = post.video_url if post.is_video else post.url
            r = requests.get(url)
            bio = BytesIO(r.content)
            bio.name = "media.mp4" if post.is_video else "media.jpg"
            await update.message.reply_document(bio)
            break  # send only one for demo
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("story", story))
    app.add_handler(CommandHandler("hashtag", hashtag))
    app.run_polling()

if __name__ == "__main__":
    main()
