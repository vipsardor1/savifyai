import os
import telebot
import instaloader

BOT_TOKEN = "8322910331:AAGqv-tApne2dppAfLv2-DN62wEsCwzqM98"  # <-- shu yerga o'z tokeningni yoz
bot = telebot.TeleBot(BOT_TOKEN)

# vaqtinchalik yuklash papkasi
TMP_DIR = "/tmp/insta"
os.makedirs(TMP_DIR, exist_ok=True)

@bot.message_handler(func=lambda msg: "instagram.com" in msg.text)
def handle_instagram(msg):
    url = msg.text.strip()
    bot.send_message(msg.chat.id, "📸 Yuklanmoqda... kuting...")

    try:
        # Instaloader sozlamalari
        loader = instaloader.Instaloader(dirname_pattern=TMP_DIR)
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=TMP_DIR)

        # Yuklangan fayllarni topamiz
        files = [os.path.join(TMP_DIR, f) for f in os.listdir(TMP_DIR)]

        # Hech narsa topilmasa
        if not files:
            bot.send_message(msg.chat.id, "⚠️ Hech qanday rasm yoki video topilmadi.")
            return

        # Fayllarni ajratib yuborish
        for file in files:
            if file.endswith((".jpg", ".jpeg", ".png")):
                with open(file, "rb") as img:
                    bot.send_photo(msg.chat.id, img)
            elif file.endswith(".mp4"):
                with open(file, "rb") as vid:
                    bot.send_video(msg.chat.id, vid)

        # Tozalash
        for file in files:
            os.remove(file)

    except Exception as e:
        bot.send_message(msg.chat.id, f"⚠️ Xato: {e}")

bot.polling()

