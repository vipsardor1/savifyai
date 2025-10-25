import os
import re
import logging
import json
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.types import Message
from yt_dlp import YoutubeDL
from instaloader import Instaloader, Profile, LoginRequiredException

# --- Настройка ---
logging.basicConfig(level=logging.INFO) # Изменено на INFO, чтобы видеть больше логов
log = logging.getLogger(__name__)

API_ID = "10107848"
API_HASH = "338de3a186b820d9ec9e73b5ef747501"
BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"
INSTA_USERNAME = "savifyai"

# (Рекомендуется) Имя пользователя вашего Instagram-аккаунта
INSTA_USERNAME = os.environ.get("INSTA_USERNAME", "savifyai") # Используйте ваш логин

def create_cookie_file():
    """Reads the cookie data from env and writes it to a file."""
    cookie_data = os.environ.get('INSTA_COOKIE_DATA')
    cookie_file_path = "instagram_cookie.txt"

    if cookie_data:
        try:
            with open(cookie_file_path, "w", encoding="utf-8") as f:
                f.write(cookie_data)
            log.info("Instagram cookie file created successfully from env variable.")
        except Exception as e:
            log.error(f"Failed to write cookie file: {e}")
    else:
        # This is the warning you are seeing now
        log.warning("INSTA_COOKIE_DATA not set. Cookie file not created.")
app = Client("saveasbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- Сообщения ---
MSG_START = "Send a link to an Instagram, TikTok, or Pinterest post. I will extract the photo, video, story, or text in a few seconds!"
MSG_PROCESSING = "⏳"
MSG_ERROR_DEFAULT = "Ошибка: Не удалось скачать. Проверьте ссылку или попробуйте другую."

# --- Regex для ссылок ---
# (Улучшен, чтобы ловить больше ссылок TikTok и Pinterest)
URL_PATTERNS = [
    r"https?://(?:www\.)?instagram\.com/(?:p|reel|tv|stories)/[A-Za-z0-9_.-]+/?(?:/\d+)?",
    r"https?://(?:www\.)?(?:vm|vt)\.tiktok\.com/[A-Za-z0-9]+/?",
    r"https?://(?:www\.)?tiktok\.com/@[A-Za-z0-9_.]+/video/\d+",
    r"https?://(?:www\.)?(?:pin\.it|pinterest\.com)/pin/\d+/?",
]
URL_REGEX = '|'.join(URL_PATTERNS)

# --- Настройка Instaloader (с аутентификацией) ---
L = Instaloader(download_video_thumbnails=False, download_geotags=False, save_metadata=False)
COOKIE_FILE = "instagram_cookie.txt"

try:
    if os.path.exists(COOKIE_FILE) and INSTA_USERNAME:
        L.load_session_from_file(username=INSTA_USERNAME, filename=COOKIE_FILE)
        log.info(f"Instaloader: Успешно загружена сессия для {INSTA_USERNAME}")
    else:
        log.warning("Instaloader: Файл куки не найден. Загрузка сторис и приватных постов не удастся.")
except Exception as e:
    log.error(f"Instaloader: Не удалось загрузить сессию: {e}")

# --- Логика бота ---

async def extract_content(url: str, message: Message):
    temp_dir = f"temp_downloads/{message.id}"
    os.makedirs(temp_dir, exist_ok=True)

    # 2. Основной метод скачивания (yt-dlp)
    log.info(f"[{message.id}] Запрос к yt-dlp")
    ydl_opts = {
        'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None, # ВАЖНО: Используем куки
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            caption = info.get('description') or info.get('title') or ""
            
            if not os.path.exists(file_path):
                 # yt-dlp иногда сохраняет с другим расширением (напр. .mp4 вместо .webm)
                 found_files = [f for f in os.listdir(temp_dir) if f.startswith(info.get('id'))]
                 if not found_files:
                     raise Exception("Файл не найден после скачивания.")
                 file_path = os.path.join(temp_dir, found_files[0])

            ext = info.get('ext', '').lower()
            if ext in ['mp4', 'mov', 'mkv', 'webm']:
                await message.reply_video(file_path, caption=caption[:1024], supports_streaming=True)
            else:
                await message.reply_photo(file_path, caption=caption[:1024])
            
            return True # Успех

    except Exception as e:
        log.error(f"[{message.id}] Ошибка yt-dlp: {e}")
        # ВОТ ГЛАВНОЕ ИЗМЕНЕНИЕ: Отправляем ошибку пользователю
        error_text = str(e)
        if "login required" in error_text.lower() or "403" in error_text:
             await message.reply("Ошибка: Этот контент приватный или требует входа. (Убедитесь, что куки-файл 'instagram_cookie.txt' существует и актуален)")
        elif "429" in error_text or "rate limit" in error_text:
             await message.reply("Ошибка: Слишком много запросов. Instagram/TikTok временно заблокировал меня. Попробуйте позже.")
        else:
             await message.reply(f"Error: Failed to download.\n\n`{error_text[:200]}...`")
        return False # Неудача

    finally:
        # Очистка временной папки
        if os.path.exists(temp_dir):
            try:
                for f in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, f))
                os.rmdir(temp_dir)
            except Exception as e:
                log.error(f"Не удалось очистить папку {temp_dir}: {e}")


@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    await message.reply(MSG_START)

@app.on_message(filters.private & filters.text & filters.regex(URL_REGEX))
async def url_handler(client: Client, message: Message):
    url = message.text.strip()
    processing_msg = await message.reply(MSG_PROCESSING) # Сохраняем сообщение
    
    success = await extract_content(url, message)
    
    # Удаляем сообщение "Обработка..."
    await processing_msg.delete()
    
    if not success:
        log.warning(f"Итоговая ошибка для {url}")
        # Сообщение об ошибке уже отправлено из extract_content
        pass

if __name__ == "__main__":
    create_cookie_file()
    log.info("Запуск бота...")
    app.run()
