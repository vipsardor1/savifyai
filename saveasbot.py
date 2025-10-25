import os
import re
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from yt_dlp import YoutubeDL
from instaloader import Instaloader, Profile

logging.basicConfig(level=logging.WARNING)

API_ID = "10107848"
API_HASH = "338de3a186b820d9ec9e73b5ef747501"
BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"

app = Client("saveasbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

MSG_START = "Отправьте ссылку на пост Instagram, TikTok или Pinterest. Я извлеку фото, видео, сторис или текст за пару секунд!"
MSG_PROCESSING = "Обработка... ⏳"
MSG_ERROR = "Ошибка: Не удалось скачать. Проверьте ссылку или попробуйте другую."

URL_PATTERNS = [
    r"https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/[A-Za-z0-9_-]+/?",
    r"https?://(?:www\.)?instagram\.com/stories/[A-Za-z0-9_.]+/\d+/?",
    r"https?://(?:www\.)?tiktok\.com/@[A-Za-z0-9_.]+/video/\d+/?",
    r"https?://(?:www\.)?pinterest\.com/pin/\d+/?",
]
URL_REGEX = '|'.join(URL_PATTERNS)

async def extract_content(url: str, message: Message):
    os.makedirs("temp_downloads", exist_ok=True)
    
    ydl_opts = {
        'outtmpl': 'temp_downloads/%(id)s.%(ext)s',
        'format': 'best[height<=1080]',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    if "instagram.com/stories" in url:
        try:
            L = Instaloader(download_video_thumbnails=False, download_geotags=False)
            parts = url.split('/')
            username = parts[-2] if parts[-2] != 'stories' else parts[-3]
            story_id = parts[-1].rstrip('/')
            
            profile = Profile.from_username(L.context, username)
            for story in profile.get_stories():
                for item in story.get_items():
                    if str(item.mediaid) in story_id:
                        file_path = f"temp_downloads/{item.mediaid}.{'mp4' if item.is_video else 'jpg'}"
                        L.download_storyitem(item, "temp_downloads")
                        if item.is_video:
                            await message.reply_video(file_path, caption="Сторис извлечена!")
                        else:
                            await message.reply_photo(file_path, caption="Сторис извлечена!")
                        os.remove(file_path)
                        return True
        except Exception:
            pass
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            caption = info.get('description') or info.get('title') or ""
            
            if info.get('duration') is not None:
                await message.reply_video(file_path, caption=caption[:1024], supports_streaming=True)
            else:
                await message.reply_photo(file_path, caption=caption[:1024])
            
            os.remove(file_path)
            return True
    except Exception as e:
        logging.error(f"Download error: {e}")
        return False

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply(MSG_START)

@app.on_message(filters.private & filters.text & filters.regex(URL_REGEX))
async def url_handler(client: Client, message: Message):
    url = message.text.strip()
    await message.reply(MSG_PROCESSING)
    success = await extract_content(url, message)
    if not success:
        await message.reply(MSG_ERROR)

if __name__ == "__main__":
    print("Запуск бота... (Starting bot...)")
    app.run()
