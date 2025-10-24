import os
import logging
import re
import shutil
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import instaloader

# --- CONFIGURATION ---
# !! REPLACE WITH YOUR TELEGRAM BOT TOKEN !!
TELEGRAM_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98" 

# !! (RECOMMENDED) ADD YOUR INSTAGRAM USERNAME AND PASSWORD !!
# This is crucial for reliability.
INSTA_USERNAME = "your_insta_username" 
INSTA_PASSWORD = "your_insta_password"

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- INSTALOADER SETUP ---
L = instaloader.Instaloader(
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    post_metadata_txt_pattern="",
    max_connection_attempts=1,
)

# Try to log in to Instagram
try:
    L.login(INSTA_USERNAME, INSTA_PASSWORD)
    logger.info(f"Successfully logged in to Instagram as {INSTA_USERNAME}")
except Exception as e:
    logger.warning(f"Could not log in to Instagram: {e}. Bot will run unauthenticated.")
    logger.warning("Expect errors and rate-limiting!")


# --- BOT HANDLERS ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Hi! I'm an Instagram downloader bot. 📸\n\n"
        "Send me a link to an Instagram post, and I'll download it for you.\n\n"
        "**Commands:**\n"
        "➤ `/post <url>` - Downloads a single post.\n"
        "➤ `/profile <username>` - Gets profile info and pic.\n\n"
        "Just sending a post URL will also work!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the help message."""
    await start_command(update, context) # Just re-use the start message

async def get_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches and sends profile information."""
    if not context.args:
        await update.message.reply_text("Please provide a username.\nUsage: `/profile <username>`")
        return

    username = context.args[0]
    await update.message.reply_text(f"Fetching profile for *{username}*...", parse_mode='Markdown')

    try:
        profile = instaloader.Profile.from_username(L.context, username)
        
        caption = (
            f"👤 *{profile.full_name}* (@{profile.username})\n"
            f"bio: _{profile.biography}_\n\n"
            f"★ *{profile.followers}* followers\n"
            f"★ *{profile.followees}* following\n"
            f"★ *{profile.mediacount}* posts\n"
            f"🔗 {profile.external_url}"
        )
        
        # Send profile pic and caption
        await update.message.reply_photo(
            photo=profile.get_profile_pic_url(),
            caption=caption,
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Error fetching profile {username}: {e}")
        await update.message.reply_text(f"Could not fetch profile '{username}'. Is it correct and public?")


def extract_shortcode(url: str) -> str | None:
    """Extracts the post shortcode from various Instagram URL formats."""
    match = re.search(r"/(p|reel|tv)/([A-Za-z0-9-_]+)", url)
    if match:
        return match.group(2)
    return None

async def download_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Downloads and sends a single Instagram post."""
    url = ""
    if context.args:
        # Came from /post command
        url = context.args[0]
    elif update.message.text:
        # Came from a plain text message
        url = update.message.text
        
    shortcode = extract_shortcode(url)

    if not shortcode:
        await update.message.reply_text("That doesn't look like a valid Instagram post URL. 🤔")
        return

    await update.message.reply_text("Got it! Downloading post...")
    
    # Create a temporary directory to download into
    # This keeps downloads from different users separate
    download_dir = f"temp_{shortcode}"

    try:
        # Get post object
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        # Download the post
        L.download_post(post, target=download_dir)
        
        media_files = []
        media_group = []
        
        # Find the downloaded files (images and videos)
        for filename in os.listdir(download_dir):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                path = os.path.join(download_dir, filename)
                media_files.append(path)
                media_group.append(InputMediaPhoto(media=open(path, 'rb')))
            elif filename.endswith('.mp4'):
                path = os.path.join(download_dir, filename)
                media_files.append(path)
                media_group.append(InputMediaVideo(media=open(path, 'rb')))

        if not media_files:
            await update.message.reply_text("Could not find any media in that post.")
            return

        # Send the media
        if len(media_group) == 1:
            # Send single photo or video
            if media_files[0].endswith('.mp4'):
                await update.message.reply_video(video=open(media_files[0], 'rb'), caption=post.caption)
            else:
                await update.message.reply_photo(photo=open(media_files[0], 'rb'), caption=post.caption)
        else:
            # Send as an album (media group)
            # Add caption to the first item only
            media_group[0].caption = post.caption
            await update.message.reply_media_group(media=media_group)

    except Exception as e:
        logger.error(f"Error downloading post {shortcode}: {e}")
        await update.message.reply_text(f"Sorry, I couldn't download that post. Is the account private or is the post deleted?")
    
    finally:
        # --- CRITICAL: Clean up the downloaded files ---
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)
            logger.info(f"Cleaned up directory: {download_dir}")


def main():
    """Start the bot."""
    
    # Make sure token is set
    if TELEGRAM_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("!!! BOT TOKEN IS NOT SET. Please edit the bot.py file. !!!")
        return
        
    logger.info("Starting bot...")
    
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # --- Register Handlers ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", get_profile))
    application.add_handler(CommandHandler("post", download_post))

    # Add a handler for plain text messages containing Instagram URLs
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & (filters.Regex(r"instagram.com/(p|reel|tv)/")), 
            download_post
        )
    )

    # Run the bot until you press Ctrl-C
    logger.info("Bot is running. Press Ctrl-C to stop.")
    application.run_polling()


if __name__ == "__main__":
    main()
