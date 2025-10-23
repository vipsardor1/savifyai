#!/usr/bin/env python3
import os
import logging
import tempfile
import subprocess
from pathlib import Path
import requests

from telegram import Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Local import (place acr.py next to this file)
from acr import recognize_audio_acr

# Config from environment
BOT_TOKEN = os.environ.get("8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98")
# Optionally provide insta username/password if you expect to download private content:
INSTA_USERNAME = os.environ.get("INSTA_USERNAME")
INSTA_PASSWORD = os.environ.get("INSTA_PASSWORD")

if not BOT_TOKEN:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN environment variable")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Hi! Send me an Instagram URL and I'll download the media for you.\n"
        "Send an audio file to identify the song (Shazam-like)."
    )

def is_instagram_url(text: str) -> bool:
    return "instagram.com" in (text or "")

def download_instagram(url: str, outdir: str) -> list:
    """
    Uses yt-dlp to download Instagram media into outdir. Returns list of file paths.
    """
    # Build command for best quality
    # -f bestvideo+bestaudio/best
    # --merge-output-format mp4 to ensure playable file
    # --no-playlist so if user sends a profile we avoid everything
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", str(Path(outdir) / "%(id)s.%(ext)s"),
        url
    ]

    # If credentials provided, pass them
    if INSTA_USERNAME and INSTA_PASSWORD:
        cmd.insert(1, "--username")
        cmd.insert(2, INSTA_USERNAME)
        cmd.insert(3, "--password")
        cmd.insert(4, INSTA_PASSWORD)

    logger.info("Running yt-dlp: %s", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        logger.error("yt-dlp error: %s", proc.stderr)
        raise RuntimeError(f"yt-dlp failed: {proc.stderr.strip()[:200]}")
    # find output files in outdir
    files = list(Path(outdir).glob("*"))
    return [str(p) for p in files]

def handle_text(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if is_instagram_url(text):
        msg = update.message.reply_text("Downloading from Instagram, please wait...")
        with tempfile.TemporaryDirectory() as tmp:
            try:
                downloaded = download_instagram(text, tmp)
            except Exception as e:
                logger.exception("Download failed")
                msg.edit_text(f"Failed to download: {e}")
                return
            # Send files back
            for fpath in downloaded:
                f = Path(fpath)
                mime = f.suffix.lower()
                if mime in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
                    update.message.reply_photo(photo=open(fpath, "rb"))
                else:
                    # video or other: send as video
                    update.message.reply_video(video=open(fpath, "rb"))
            msg.edit_text("Done ✅")
    else:
        update.message.reply_text("Send a valid Instagram post/reel URL or an audio file to identify music.")

def handle_audio(update: Update, context: CallbackContext):
    # Accept audio or voice
    message = update.message
    audio_file = None
    if message.voice:
        audio_file = message.voice.get_file()
    elif message.audio:
        audio_file = message.audio.get_file()
    elif message.document:
        # possibly an audio file sent as doc
        audio_file = message.document.get_file()
    else:
        update.message.reply_text("Send an audio file (mp3/wav/ogg) or voice message.")
        return

    status = update.message.reply_text("Downloading audio to analyze...")
    with tempfile.TemporaryDirectory() as tmp:
        local_path = Path(tmp) / "input_audio"
        audio_file.download(str(local_path))
        # convert to wav if needed using pydub (ffmpeg required)
        try:
            from pydub import AudioSegment
            from pathlib import Path
            p = Path(local_path)
            # detect extension / convert to wav of acceptable sample rate
            ext = p.suffix.lower() or ".ogg"
            if ext not in [".wav", ".mp3", ".ogg", ".m4a", ".flac"]:
                # try to assume ogg
                ext = ".ogg"
                p = p.with_suffix(ext)
            # ensure .wav
            src = str(local_path)
            wav_out = str(Path(tmp) / "audio.wav")
            sound = AudioSegment.from_file(src)
            sound = sound.set_frame_rate(44100).set_channels(1)
            sound.export(wav_out, format="wav")
            wav_path = wav_out
        except Exception as e:
            logger.exception("pydub conversion failed")
            status.edit_text(f"Failed to convert audio: {e}")
            return

        status.edit_text("Submitting to music-recognition service...")
        try:
            result = recognize_audio_acr(wav_path)  # returns dict with results or raises
        except Exception as e:
            logger.exception("Recognition failed")
            status.edit_text(f"Recognition failed: {e}")
            return

        # Parse & reply
        if not result:
            status.edit_text("No match found.")
            return
        # example structure: {'title': 'Song', 'artist': 'Artist', 'album': '...', 'score': 100}
        reply_lines = []
        # ACRCloud returns complex JSON; acr.py will normalize common fields
        if "title" in result:
            reply_lines.append(f"Title: {result.get('title')}")
        if "artist" in result:
            reply_lines.append(f"Artist: {result.get('artist')}")
        if "album" in result:
            reply_lines.append(f"Album: {result.get('album')}")
        if "score" in result:
            reply_lines.append(f"Confidence: {result.get('score')}")
        if "release_date" in result:
            reply_lines.append(f"Release: {result.get('release_date')}")
        if "acrid_link" in result:
            reply_lines.append(f"Link: {result.get('acrid_link')}")
        status.edit_text("\n".join(reply_lines))

def error_handler(update: object, context: CallbackContext):
    logger.error("Exception while handling an update:", exc_info=context.error)
    # notify user
    try:
        update.message.reply_text("An error occurred. Sorry.")
    except Exception:
        pass

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    dp.add_handler(MessageHandler(Filters.voice | Filters.audio | Filters.document.category("audio"), handle_audio))
    dp.add_error_handler(error_handler)

    updater.start_polling()
    logger.info("Bot started")
    updater.idle()

if __name__ == "__main__":
    main()
