#!/usr/bin/env ./venv/bin/python3
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)
from telnet_script import query_onu_status

# Load environment variables
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
AUTHORIZED_ID = os.getenv("AUTHORIZED_USER_ID", "").strip()

print(f"--- Bot Debug Info ---")
print(f"Authorized ID: '{AUTHORIZED_ID}'")
print(f"Token: {(TOKEN[:10] + '...') if TOKEN else 'NOT_FOUND'}")
print(f"----------------------")

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Conversation States
WAITING_FOR_SN = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command."""
    user_id = str(update.effective_user.id)
    logging.info(f"Incoming /start from user_id: {user_id}")
    
    if user_id != AUTHORIZED_ID:
        logging.warning(f"Unauthorized access attempt by {user_id}")
        await update.message.reply_text(f"⛔ Akses ditolak. ID Anda ({user_id}) tidak terdaftar.")
        return

    await update.message.reply_text(
        "👋 Halo! Saya Bot Manajemen OLT.\n"
        "Gunakan perintah /onu untuk mulai mengecek status ONU."
    )

async def onu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /onu command."""
    user_id = str(update.effective_user.id)
    logging.info(f"Incoming /onu from user_id: {user_id}")
    
    if user_id != AUTHORIZED_ID:
        logging.warning(f"Unauthorized access attempt by {user_id}")
        await update.message.reply_text(f"⛔ Akses ditolak. ID Anda ({user_id}) tidak terdaftar.")
        return ConversationHandler.END

    await update.message.reply_text("🔍 Silakan masukkan Serial Number (SN) ONU:")
    return WAITING_FOR_SN

async def handle_sn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the SN input and queries the OLT."""
    sn = update.message.text.strip()
    user_id = str(update.effective_user.id)
    logging.info(f"Received SN: '{sn}' from user_id: {user_id}")
    
    # Feedback awal ke user
    await update.message.reply_text(f"🔍 Input diterima: <code>{sn}</code>\n⏳ Sedang diproses ke OLT...", parse_mode='HTML')
    
    try:
        # Call telnet script
        result = await query_onu_status(sn)
        
        # Format and send response
        if result:
            # Menggunakan triple backticks dan HTML escaping (minimal) untuk keamanan karakter khusus
            message = f"✅ <b>Hasil dari OLT:</b>\n\n<pre>{result}</pre>"
            await update.message.reply_text(message, parse_mode='HTML')
        else:
            await update.message.reply_text("⚠️ OLT tidak mengembalikan data (kosong).")
            
    except Exception as e:
        error_msg = f"❌ <b>Terjadi Kesalahan Internal Bot:</b>\n<code>{str(e)}</code>"
        await update.message.reply_text(error_msg, parse_mode='HTML')
        logging.error(f"Error in handle_sn: {e}")

    return ConversationHandler.END

async def debug_catcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Logs EVERYTHING the bot receives."""
    if update.message:
        logging.info(f"DEBUG: Received message: '{update.message.text}' from {update.effective_user.id}")
    elif update.callback_query:
        logging.info(f"DEBUG: Received callback: '{update.callback_query.data}'")
    else:
        logging.info(f"DEBUG: Received update: {update.update_id}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ends the conversation."""
    await update.message.reply_text("Selesai.")
    return ConversationHandler.END

if __name__ == "__main__":
    if not TOKEN or TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Error: Harap isi TELEGRAM_TOKEN di file .env")
        exit(1)

    print("Bot is running...")
    
    # Startup notification to user
    async def post_init(application):
        if AUTHORIZED_ID:
            try:
                await application.bot.send_message(
                    chat_id=AUTHORIZED_ID, 
                    text="🚀 <b>Bot Baru Saja Aktif!</b>\nSaya siap menerima perintah.",
                    parse_mode='HTML'
                )
                print(f"Startup notification sent to {AUTHORIZED_ID}")
            except Exception as e:
                print(f"Failed to send startup notification: {e}")

    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # Simplifikasi: Pakai handler biasa dulu, jangan ConversationHandler agar tidak bingung state
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("onu", onu_command))
    # Catch-all untuk SN (atau teks apapun)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_sn))
    
    # Debug catcher semua
    app.add_handler(MessageHandler(filters.ALL, debug_catcher), group=-1)

    app.run_polling()
