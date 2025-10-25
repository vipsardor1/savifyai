import os
import re
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from yt_dlp import YoutubeDL
from instaloader import Instaloader, Profile, Story, Post
import asyncio

# Configure logging (minimal, like original)
logging.basicConfig(level=logging.WARNING)

# Bot config (use env vars for security)
API_ID = int "10107848"  # From my.telegram.org
API_HASH = "338de3a186b820d9ec9e73b5ef747501"
BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"  # From @BotFather

app = Client("saveas_clone", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Russian messages for exact match
MSG_START = "Отправьте ссылку на пост Instagram, TikTok или Pinterest. Я извлеку фото, видео, сторис или текст за пару секунд!"
MSG_PROCESSING = "Обработка... ⏳"
MSG_ERROR = "Ошибка: Не удалось скачать. Проверьте ссылку или попробуйте другую."

# URL patterns for platforms (exact to @SaveAsBot)
URL_PATTERNS = [
    r"https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[A-Za-z0-9_-]+/?",  # Posts, Reels, IGTV
    r"https?://(?:www\.)?instagram\.com/stories/[A-Za-z0-9_.]+/\d+/?",   # Stories
    r"https?://(?:www\.)?tiktok\.com/@[A-Za-z0-9_.]+/video/\d+/?",       # TikTok videos
    r"https?://(?:www\.)?pinterest\.com/pin/\d+/?",                       # Pinterest pins
]

# Combined regex for filtering
URL_REGEX = '|'.join(URL_PATTERNS)

# Download function (core logic, optimized for speed)
async def extract_content(url: str, message: Message):
    os.makedirs("temp_downloads", exist_ok=True)
    
    # yt-dlp options (high quality, no playlist, fast)
    ydl_opts = {
        'outtmpl': 'temp_downloads/%(id)s.%(ext)s',
        'format': 'best[height<=1080]',  # Balances quality/size for Telegram
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    # Special handling for Instagram stories (use instaloader for precision)
    if "instagram.com/stories" in url:
        try:
            L = Instaloader(download_video_thumbnails=False, download_geotags=False)
            # Extract username and story ID from URL
            parts = url.split('/')
            username = parts[-2] if parts[-2] != 'stories' else parts[-3]
            story_id = int(parts[-1])
            
            profile = Profile.from_username(L.context, username)
            for story in profile.get_stories():
                for item in story.get_items():
                    if item.date_utc.timestamp() >= (story_id / 1000):  # Approximate match
                        file_path = f"temp_downloads/{username}_story_{item.date_utc}.jpg"
                        L.download_storyitem(item, f"temp_downloads")
                        await message.reply_photo(file_path, caption="Сторис извлечена!")
                        os.remove(file_path)
                        return
        except Exception:
            pass  # Fallback to yt-dlp
    
    # Fallback: yt-dlp for all (handles posts, Reels, IGTV, TikTok, Pinterest)
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            # Determine media type and extract text if present
            is_video = info.get('duration') is not None
            text_caption = info.get('description') or info.get('title') or ""
            
            # Send as file for max quality (like @SaveAsBot)
            if is_video:
                await message.reply_video(file_path, caption=text_caption[:1024], supports_streaming=True)
            else:
                await message.reply_photo(file_path, caption=text_caption[:1024])
            
            # Cleanup
            os.remove(file_path)
            return True
    except Exception as e:
        logging.error(f"Download error: {e}")
        return False

# /start handler (optional, like original)
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply(MSG_START)

# Main URL handler (triggers on any matching link, exact behavior)
@app.on_message(filters.private & filters.text & filters.regex(URL_REGEX))
async def url_handler(client: Client, message: Message):
    url = message.text.strip()
    await message.reply(MSG_PROCESSING)
    
    success = await extract_content(url, message)
    if not success:
        await message.reply(MSG_ERROR)

# Run the bot
if __name__ == "__main__":
    print("Запуск бота... (Starting bot...)")
    app.run()
