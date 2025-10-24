import os
import logging
import re
import shutil
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import instaloader

# --- CONFIGURATION ---
# !! THESE WILL BE SET IN RAILWAY, NOT HERE !!
TELEGRAM_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"
INSTA_USERNAME = "savifyai"
INSTA_PASSWORD = "200502saxx"

# --- NEW: Define persistent storage paths ---
# We will tell Railway to create a volume at /app/storage
STORAGE_DIR = "/app/storage"
SESSION_FILE = os.path.join(STORAGE_DIR, f"{INSTA_USERNAME}.session")

# Ensure the storage directory exists
os.makedirs(STORAGE_DIR, exist_ok=True) 

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

# --- NEW: Persistent Login Logic ---
try:
    if os.path.exists(SESSION_FILE):
        logger.info(f"Loading session from file: {SESSION_FILE}")
        L.load_session_from_file(INSTA_USERNAME, SESSION_FILE)
        L.test_login() # Test if the session is still valid
        logger.info(f"Successfully loaded session for {INSTA_USERNAME}")
    else:
        logger.info("Session file not found, logging in with credentials...")
        L.login(INSTA_USERNAME, INSTA_PASSWORD)
        logger.info(f"Successfully logged in as {INSTA_USERNAME}")
        L.save_session_to_file(SESSION_FILE)
        logger.info(f"Session saved to {SESSION_FILE}")

except Exception as e:
    logger.error(f"Error during Instagram login: {e}")
    logger.warning("Bot might be unauthenticated and will likely fail.")
    # If login fails, try to proceed unauthenticated (will be rate-limited)
    pass
# --- END OF NEW LOGIN LOGIC ---


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
        url = context.args[0]
    elif update.message.text:
        url = update.message.text
        
    shortcode = extract_shortcode(url)

    if not shortcode:
        await update.message.reply_text("That doesn't look like a valid Instagram post URL. 🤔")
        return

    await update.message.reply_text("Got it! Downloading post...")
    
    # --- MODIFIED: Use the persistent storage for temp downloads ---
    download_dir = os.path.join(STORAGE_DIR, f"temp_{shortcode}")

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=download_dir)
        
        media_files = []
        media_group = []
        
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

        if len(media_group) == 1:
            if media_files[0].endswith('.mp4'):
                await update.message.reply_video(video=open(media_files[0], 'rb'), caption=post.caption)
            else:
                await update.message.reply_photo(photo=open(media_files[0], 'rb'), caption=post.caption)
        else:
            media_group[0].caption = post.caption
            await update.message.reply_media_group(media=media_group)

    except Exception as e:
        logger.error(f"Error downloading post {shortcode}: {e}")
        await update.message.reply_text(f"Sorry, I couldn't download that post. Is the account private or is the post deleted?")
    
    finally:
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)
            logger.info(f"Cleaned up directory: {download_dir}")


def main():
    """Start the bot."""
    
    # --- MODIFIED: Check for environment variables ---
    if not TELEGRAM_TOKEN or not INSTA_USERNAME or not INSTA_PASSWORD:
        logger.error("!!! MISSING ENVIRONMENT VARIABLES !!!")
        logger.error("Please set TELEGRAM_TOKEN, INSTA_USERNAME, and INSTA_PASSWORD in Railway.")
        return
        
    logger.info("Starting bot...")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", get_profile))
    application.add_handler(CommandHandler("post", download_post))

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & (filters.Regex(r"instagram.com/(p|reel|tv)/")), 
            download_post
        )
    )

    logger.info("Bot is running. Press Ctrl-C to stop.")
    application.run_polling()


if __name__ == "__main__":
    main()
