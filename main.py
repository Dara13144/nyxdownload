import telebot
from telebot import types
import yt_dlp
import os
import uuid

# Configuration
API_TOKEN = '8674498789:AAGdESr3uBIGjuWhw1aI03LrpivZ1gB8z40'
bot = telebot.TeleBot(API_TOKEN)

# Dictionary to store user's URL temporarily
user_data = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 Send me a video link (YouTube, TikTok, Instagram, etc.) to download!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text
    if "http" in url:
        user_data[message.chat.id] = url
        
        # Create Inline Buttons
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_video = types.InlineKeyboardButton("🎥 Download Video", callback_data="dl_video")
        btn_audio = types.InlineKeyboardButton("🎵 Download MP3", callback_data="dl_audio")
        markup.add(btn_video, btn_audio)
        
        bot.send_message(message.chat.id, "Select format:", reply_markup=markup)
    else:
        bot.reply_to(message, "❌ Please send a valid URL.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    url = user_data.get(chat_id)
    
    if not url:
        bot.answer_callback_query(call.id, "Error: URL not found. Please resend the link.")
        return

    bot.edit_message_text("⏳ Processing... please wait.", chat_id, call.message.message_id)
    
    # Generate unique filename to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    
    if call.data == "dl_video":
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'video_{unique_id}.%(ext)s',
            'max_filesize': 50 * 1024 * 1024  # 50MB limit for Telegram bots
        }
        download_and_send(chat_id, url, ydl_opts, is_video=True)
        
    elif call.data == "dl_audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'audio_{unique_id}.%(ext)s',
        }
        download_and_send(chat_id, url, ydl_opts, is_video=False)

def download_and_send(chat_id, url, ydl_opts, is_video):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Adjust filename for MP3 post-processing
            if not is_video:
                filename = filename.rsplit('.', 1)[0] + ".mp3"

        with open(filename, 'rb') as f:
            if is_video:
                bot.send_video(chat_id, f, caption="✅ Video Downloaded!")
            else:
                bot.send_audio(chat_id, f, caption="✅ Audio Downloaded!")
        
        # Cleanup file after sending
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
