import os
import logging
import re
import shutil
import json
import ffmpeg
import yt_dlp
import instaloader
from acrcloud.recognizer import ACRCloudRecognizer
from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- CONFIGURATION (READ FROM RAILWAY ENV VARIABLES) ---
TELEGRAM_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"
INSTA_USERNAME = "savifyai"
INSTA_PASSWORD = "200502saxx"
ACR_HOST = "identify-ap-southeast-1.acrcloud.com"
ACR_ACCESS_KEY = "545a16c7521fff56816c396f5e4eeb5a"
ACR_SECRET_KEY = "517hIieKi6OhiLSMj16fn6cTJYeqtA8nrtFdmtBb"

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

# --- STARTUP FUNCTIONS ---

def login_instaloader():
    """Logs in to Instaloader using credentials from env variables."""
    if INSTA_USERNAME and INSTA_PASSWORD:
        try:
            L.login(INSTA_USERNAME, INSTA_PASSWORD)
            logger.info(f"Instaloader successfully logged in as {INSTA_USERNAME}")
        except Exception as e:
            logger.error(f"Instaloader login failed: {e}. Stories/private content will fail.")
    else:
        logger.warning("INSTA_USERNAME or INSTA_PASSWORD not set. Instaloader is unauthenticated.")

def create_cookie_file():
    """Creates yt-dlp cookie file from env variable (for Railway)."""
    cookie_data = os.environ.get('INSTA_COOKIE_DATA')
    if cookie_data:
        try:
            with open("instagram_cookies.txt", "w", encoding="utf-8") as f:
                f.write(cookie_data)
            logger.info("yt-dlp cookie file created successfully.")
        except Exception as e:
            logger.error(f"Failed to write yt-dlp cookie file: {e}")
    else:
        logger.warning("INSTA_COOKIE_DATA not set. yt-dlp may fail on Instagram.")


# --- BOT HANDLERS (COMMANDS) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message."""
    await update.message.reply_text(
        "Hi! I am a multi-platform downloader and song identifier. 🤖\n\n"
        "**MEDIA DOWNLOADING**\n"
        "Just send me a link from:\n"
        "• TikTok\n"
        "• YouTube (Videos, Shorts)\n"
        "• Instagram (Posts, Reels)\n"
        "• Threads, Pinterest, and more!\n\n"
        "**INSTAGRAM COMMANDS**\n"
        "➤ `/profile <username>` - Get profile info.\n"
        "➤ `/stories <username>` - Download current stories.\n\n"
        "**SONG RECOGNITION** 🎵\n"
        "Send me any audio, voice message, or video, and I'll tell you the song!",
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the help message."""
    await start_command(update, context)


# --- BOT HANDLERS (MESSAGES) ---

async def handle_message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks message text for a URL and routes to the correct downloader."""
    message_text = update.message.text
    
    # Regex for Instagram Post/Reel
    insta_match = re.search(r"instagram.com/(p|reel|tv)/([A-Za-z0-9-_]+)", message_text)
    
    # Generic URL match
    url_match = re.search(r"https://\S+|http://\S+", message_text)

    if insta_match:
        # It's an Instagram post, use the specialized Instaloader function
        shortcode = insta_match.group(2)
        logger.info(f"Routing to Instaloader for shortcode: {shortcode}")
        await download_insta_post(update, context, shortcode)
        
    elif "instagram.com/" in message_text:
        # Other Instagram link (e.g., profile) - tell user to use commands
        await update.message.reply_text(
            "For Instagram profiles or stories, please use the commands:\n"
            "• `/profile <username>`\n"
            "• `/stories <username>`"
        )
        
    elif url_match:
        # It's another URL, use the generic yt-dlp downloader
        url = url_match.group(0)
        logger.info(f"Routing to yt-dlp for URL: {url}")
        await download_generic_video(update, context, url)
        
    else:
        # Not a command, not a URL
        await update.message.reply_text(
            "Please send me a valid link or an audio/video file."
        )

# --- INSTALOADER FUNCTIONS (Your New Code, Modified) ---

async def get_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetches and sends profile information."""
    if not context.args:
        await update.message.reply_text("Usage: `/profile <username>`")
        return

    username = context.args[0].replace('@', '')
    await update.message.reply_text(f"Fetching profile for *{username}*...", parse_mode=ParseMode.MARKDOWN)

    try:
        profile = instaloader.Profile.from_username(L.context, username)
        
        caption = (
            f"👤 *{profile.full_name}* (@{profile.username})\n"
            f"Bio: _{profile.biography}_\n\n"
            f"★ *{profile.followers}* followers\n"
            f"★ *{profile.followees}* following\n"
            f"★ *{profile.mediacount}* posts\n"
        )
        if profile.external_url:
            caption += f"🔗 {profile.external_url}"
        
        await update.message.reply_photo(
            photo=profile.get_profile_pic_url(),
            caption=caption,
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logger.error(f"Error fetching profile {username}: {e}")
        await update.message.reply_text(f"Could not fetch profile '{username}'.")


async def download_insta_post(update: Update, context: ContextTypes.DEFAULT_TYPE, shortcode: str):
    """Downloads and sends a single Instagram post using Instaloader."""
    await update.message.reply_text("Instagram post detected! Downloading...")
    
    download_dir = f"temp_insta_{shortcode}"
    
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=download_dir)
        
        media_group = []
        
        # Find downloaded files
        for filename in sorted(os.listdir(download_dir)):
            path = os.path.join(download_dir, filename)
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                media_group.append(InputMediaPhoto(media=open(path, 'rb')))
            elif filename.endswith('.mp4'):
                media_group.append(InputMediaVideo(media=open(path, 'rb')))

        if not media_group:
            await update.message.reply_text("Could not find any media in that post.")
            return

        # Add caption to the first item
        media_group[0].caption = post.caption if post.caption else ""

        # Send media
        await update.message.reply_media_group(media=media_group)

    except Exception as e:
        logger.error(f"Error downloading Instaloader post {shortcode}: {e}")
        await update.message.reply_text("Sorry, I couldn't download that post.")
    
    finally:
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)


async def download_stories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Downloads all current stories for a user."""
    if not context.args:
        await update.message.reply_text("Usage: `/stories <username>`")
        return
        
    username = context.args[0].replace('@', '')
    await update.message.reply_text(f"Fetching stories for *{username}*... ⏳", parse_mode=ParseMode.MARKDOWN)
    
    download_dir = f"temp_stories_{username}"

    try:
        profile = instaloader.Profile.from_username(L.context, username)
        if not profile.has_viewable_story:
            await update.message.reply_text(f"User *{username}* has no viewable stories.", parse_mode=ParseMode.MARKDOWN)
            return

        # Download all stories
        L.download_stories(userids=[profile.userid], filename_target=download_dir)

        media_group = []
        for filename in sorted(os.listdir(download_dir)):
            path = os.path.join(download_dir, filename)
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                media_group.append(InputMediaPhoto(media=open(path, 'rb')))
            elif filename.endswith('.mp4'):
                media_group.append(InputMediaVideo(media=open(path, 'rb')))

        if not media_group:
            await update.message.reply_text("Found stories, but failed to process media.")
            return

        await update.message.reply_text(f"Uploading {len(media_group)} stories...")
        
        # Send in chunks of 10 (Telegram media group limit)
        for i in range(0, len(media_group), 10):
            chunk = media_group[i:i+10]
            await update.message.reply_media_group(media=chunk)

    except Exception as e:
        logger.error(f"Error downloading stories for {username}: {e}")
        await update.message.reply_text(f"Could not get stories. Is the account private or do they have no stories?")
    
    finally:
        if os.path.exists(download_dir):
            shutil.rmtree(download_dir)


# --- YT-DLP DOWNLOADER (Our Old Code) ---

async def download_generic_video(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """Downloads video(s) from a URL using yt-dlp."""
    chat_id = update.message.chat_id
    await update.message.reply_text("Downloading... ⏳")

    download_path = f'./download_{chat_id}'
    
    if os.path.exists(download_path):
        shutil.rmtree(download_path)
    os.makedirs(download_path)

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(download_path, '%(id)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'logger': logger,
        'cookiefile': 'instagram_cookies.txt', # Use the cookie file we created
        'noplaylist': True, # Download single video by default
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        downloaded_files = os.listdir(download_path)
        if not downloaded_files:
            await update.message.reply_text("Hmm, download finished but no files were found.")
        
        for filename in downloaded_files:
            file_path = os.path.join(download_path, filename)
            await update.message.reply_video(video=open(file_path, 'rb'), caption="Here's your video!")

    except Exception as e:
        logger.error(f"Error downloading {url} with yt-dlp: {e}")
        await update.message.reply_text(f"Sorry, I couldn't download that. 😔\nError: {e}")
    
    finally:
        if os.path.exists(download_path):
            shutil.rmtree(download_path)


# --- SONG RECOGNITION (Our Old Code) ---

async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles an audio file or voice message for song recognition."""
    await update.message.reply_text("Got your audio! Trying to identify the song... 🎵")
    
    try:
        if update.message.audio:
            file = await update.message.audio.get_file()
        elif update.message.voice:
            file = await update.message.voice.get_file()
        else:
            return

        file_path = f"{file.file_id}.ogg"
        await file.download_to_drive(file_path)

        song_info = await recognize_song(file_path)
        
        if song_info:
            await update.message.reply_text(song_info, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("Sorry, I couldn't recognize that song. 😕")
        
        os.remove(file_path)

    except Exception as e:
        logger.error(f"Error handling audio: {e}")
        await update.message.reply_text(f"An error occurred: {e}")


async def handle_video_for_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles a video file to extract its audio for recognition."""
    await update.message.reply_text("Got video! Extracting audio to find the song... 🎵")
    
    try:
        file = await update.message.video.get_file()
        video_path = f"{file.file_id}.mp4"
        await file.download_to_drive(video_path)

        audio_path = f"{file.file_id}_audio.mp3"
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec='mp3')
            .run(overwrite_output=True, quiet=True)
        )

        song_info = await recognize_song(audio_path)
        
        if song_info:
            await update.message.reply_text(song_info, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("Sorry, I couldn't recognize that song. 😕")

        os.remove(video_path)
        os.remove(audio_path)

    except Exception as e:
        logger.error(f"Error handling video for audio: {e}")
        await update.message.reply_text(f"An error occurred: {e}")


async def recognize_song(file_path: str):
    """Recognizes a song from a file using the ACRCloud API."""
    logger.info(f"Recognizing song from {file_path} using ACRCloud...")

    config = {
        'host': ACR_HOST,
        'access_key': ACR_ACCESS_KEY,
        'access_secret': ACR_SECRET_KEY,
        'timeout': 10
    }

    if not all(config.values()):
        logger.error("ACRCloud config is missing! Check env variables.")
        return "Sorry, song recognition is not configured correctly. 😕"

    try:
        re = ACRCloudRecognizer(config)
        result_json = re.recognize_by_file(file_path, 0, 15)
        result = json.loads(result_json)

        status_code = result.get('status', {}).get('code')

        if status_code == 0:
            music_data = result.get('metadata', {}).get('music', [{}])[0]
            title = music_data.get('title')
            artists = music_data.get('artists', [{}])
            artist_names = ', '.join([artist.get('name', '') for artist in artists])
            album = music_data.get('album', {}).get('name')

            response_lines = [
                "I found it! 🎉",
                f"**Title:** {title}",
                f"**Artist(s):** {artist_names}"
            ]
            if album:
                response_lines.append(f"**Album:** {album}")
            
            return "\n".join(response_lines)
        
        elif status_code == 1001:
            return "Sorry, I listened, but I couldn't recognize that song. 😕"
        
        else:
            logger.error(f"ACRCloud error. Code: {status_code}, Msg: {result.get('status', {}).get('msg')}")
            return "Sorry, an error occurred with the song recognition service."

    except Exception as e:
        logger.error(f"Exception during song recognition: {e}")
        return f"An error occurred while trying to recognize the song: {e}"


# --- MAIN FUNCTION ---

def main():
    """Start the bot."""
    if not TELEGRAM_TOKEN:
        logger.critical("!!! TELEGRAM_TOKEN environment variable is not set. Bot cannot start. !!!")
        return

    # --- Run Startup Tasks ---
    create_cookie_file()
    login_instaloader()
    
    logger.info("Starting bot...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # --- Register Handlers ---
    # Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", get_profile))
    application.add_handler(CommandHandler("stories", download_stories))
    # Note: We removed /post, it's handled by the message router

    # Message Handlers
    # Song Recognition
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(MessageHandler(filters.VOICE, handle_audio))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video_for_audio))
    
    # URL Router (must be one of the last text handlers)
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            handle_message_router
        )
    )

    # Run the bot
    logger.info("Bot is polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
