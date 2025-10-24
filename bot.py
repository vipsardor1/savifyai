import os
import logging
import re
import shutil
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import instaloader

# --- CONFIGURATION ---
# Get token from Railway environment variables (Secure Way)
TELEGRAM_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"

# --- Define persistent storage paths ---
# This is the mount path for your Railway Volume
STORAGE_DIR = "/app/storage"
os.makedirs(STORAGE_DIR, exist_ok=True) 

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
#                         SESSION MANAGEMENT
# ----------------------------------------------------------------------

def get_session_file(user_id: int) -> str:
    """Returns the unique session file path for a given user."""
    return os.path.join(STORAGE_DIR, f"session_{user_id}.session")

async def get_user_loader(user_id: int) -> instaloader.Instaloader | None:
    """
    Loads and returns an Instaloader instance for a specific user.
    Returns None if the user is not logged in or session is expired.
    """
    session_file = get_session_file(user_id)
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
    
    if not os.path.exists(session_file):
        return None

    try:
        # We load the session using the telegram ID as a placeholder username
        L.load_session_from_file(username=str(user_id), filename=session_file)
        
        # Test the login to ensure the session is still valid
        L.test_login() 
        logger.info(f"Successfully loaded session for user {user_id}")
        return L
    except Exception as e:
        logger.warning(f"Could not load session for user {user_id}: {e}")
        # Session is likely expired or invalid, delete it
        os.remove(session_file)
        return None


# ----------------------------------------------------------------------
#                           BOT HANDLERS
# ----------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I'm an Instagram downloader bot. 📸\n\n"
        "To use me, you must first log in to your *own* Instagram account.\n\n"
        "**COMMANDS:**\n"
        "➤ `/login <username> <password>`\n"
        "   (Your password is deleted immediately)\n\n"
        "➤ `/post <url>` - Downloads a post (handles carousels).\n"
        "➤ `/profile <username>` - Gets profile info.\n"
        "➤ `/status` - Checks your login status.\n"
        "➤ `/logout` - Logs you out and deletes your session.",
        parse_mode='Markdown'
    )

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Logs a user in and saves their session."""
    user_id = update.message.from_user.id
    chat_id = update.effective_chat.id
    message_id = update.message.message_id
    
    if not context.args or len(context.args) != 2:
        await update.message.reply_text("Usage: `/login <username> <password>`")
        return

    username = context.args[0]
    password = context.args[1]
    
    # --- CRITICAL: DELETE THE PASSWORD MESSAGE ---
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass # Ignore failure if bot is not admin or in private chat
        
    await update.message.reply_text(f"Logging in as {username}... This may take a moment.")
    
    L = instaloader.Instaloader()
    session_file = get_session_file(user_id)

    try:
        L.login(username, password)
        # We save the session by the telegram ID
        L.save_session_to_file(username=str(user_id), filename=session_file)
        await update.message.reply_text(
            "✅ Login successful!\n\n"
            "Your session is saved. You can now use the bot."
        )
        
    except Exception as e:
        logger.error(f"Login failed for user {user_id}: {e}")
        await update.message.reply_text(
            f"❌ **Login Failed!**\n\n"
            f"**Error:** `{e}`\n\n"
            "If this is a 2FA error, the bot does not support 2FA."
        , parse_mode='Markdown')

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Logs a user out by deleting their session file."""
    user_id = update.message.from_user.id
    session_file = get_session_file(user_id)
    
    if os.path.exists(session_file):
        os.remove(session_file)
        await update.message.reply_text("You have been logged out. Your session file is deleted.")
    else:
        await update.message.reply_text("You are not logged in.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks if the user's session is active."""
    user_id = update.message.from_user.id
    L = await get_user_loader(user_id)
    
    if L:
        await update.message.reply_text(f"✅ You are logged in.\n(Session is active)")
    else:
        await update.message.reply_text("❌ You are not logged in. Use `/login` to start.")

async def get_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches and sends profile information."""
    user_id = update.message.from_user.id
    L = await get_user_loader(user_id)
    
    if not L:
        await update.message.reply_text("You must be logged in to use this command. Use `/login`.")
        return

    if not context.args:
        await update.message.reply_text("Usage: `/profile <username>`")
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
        logger.error(f"Error fetching profile {username} for user {user_id}: {e}")
        await update.message.reply_text(f"Could not fetch profile '{username}'. Is it correct and are you following them (if private)?")


def extract_shortcode(url: str) -> str | None:
    """Extracts the post shortcode from various Instagram URL formats."""
    match = re.search(r"/(p|reel|tv)/([A-Za-z0-9-_]+)", url)
    if match:
        return match.group(2)
    return None

async def download_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Downloads and sends a single Instagram post.
    ✅ FIX: Includes logic to send media in chunks of 10.
    """
    user_id = update.message.from_user.id
    L = await get_user_loader(user_id)
    
    if not L:
        await update.message.reply_text("You must be logged in to use this command. Use `/login <username> <password>`.")
        return

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
    
    # --- Use a unique temp dir for each user and post ---
    download_dir = os.path.join(STORAGE_DIR, f"temp_{user_id}_{shortcode}")

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=download_dir)
        
        media_group = []
        
        # Collect all downloaded media files
        for filename in sorted(os.listdir(download_dir)):
            path = os.path.join(download_dir, filename)
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                media_group.append(InputMediaPhoto(media=open(path, 'rb')))
            elif filename.endswith('.mp4'):
                media_group.append(InputMediaVideo(media=open(path, 'rb')))

        if not media_group:
            await update.message.reply_text("Could not find any media in that post. This might be a private story highlight or an unsupported format.")
            return

        # Add caption to the first item only
        if media_group:
            media_group[0].caption = post.caption

        # --- CRITICAL FIX: Loop to send in chunks of 10 (Telegram's limit) ---
        chunk_size = 10
        for i in range(0, len(media_group), chunk_size):
            chunk = media_group[i:i + chunk_size]
            
            # For chunks after the first one, clear the caption so it's not repeated
            if i > 0 and chunk[0].caption:
                chunk[0].caption = None
                
            await update.message.reply_media_group(media=chunk)
            
            # Close file handlers after sending to prevent memory leaks/file locks
            for media_item in chunk:
                 if hasattr(media_item.media, 'close'):
                    media_item.media.close()

    except Exception as e:
        logger.error(f"Error downloading post {shortcode} for user {user_id}: {e}")
        await update.message.reply_text(f"Sorry, I couldn't download that post. Is the account private or is the post deleted?")
    
    finally:
        # Cleanup the temporary directory
        if os.path.exists(download_dir):
            try:
                shutil.rmtree(download_dir)
                logger.info(f"Cleaned up directory: {download_dir}")
            except OSError as e:
                logger.warning(f"Failed to remove directory {download_dir}: {e}")


# ----------------------------------------------------------------------
#                             MAIN FUNCTION
# ----------------------------------------------------------------------

def main():
    """Start the bot."""
    
    if not TELEGRAM_TOKEN:
        logger.error("!!! TELEGRAM_TOKEN is NOT SET. Please add it to Railway environment variables. !!!")
        return
        
    logger.info("Starting bot (multi-user mode)...")
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # --- Register Handlers ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command)) # Alias
    application.add_handler(CommandHandler("login", login_command))
    application.add_handler(CommandHandler("logout", logout_command))
    application.add_handler(CommandHandler("status", status_command))
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
