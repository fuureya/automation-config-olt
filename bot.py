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
AUTHORIZED_ID = os.getenv("AUTHORIZED_USER_ID")

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
    if user_id != AUTHORIZED_ID:
        await update.message.reply_text("⛔ Akses ditolak. Anda tidak terdaftar.")
        return

    await update.message.reply_text(
        "👋 Halo! Saya Bot Manajemen OLT.\n"
        "Gunakan perintah /onu untuk mulai mengecek status ONU."
    )

async def onu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /onu command."""
    user_id = str(update.effective_user.id)
    if user_id != AUTHORIZED_ID:
        await update.message.reply_text("⛔ Akses ditolak.")
        return ConversationHandler.END

    await update.message.reply_text("🔍 Silakan masukkan Serial Number (SN) ONU:")
    return WAITING_FOR_SN

async def handle_sn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the SN input and queries the OLT."""
    sn = update.message.text.strip()
    
    await update.message.reply_text(f"⏳ Sedang mengecek SN: `{sn}` ke OLT... Mohon tunggu.")
    
    # Call telnet script
    result = await query_onu_status(sn)
    
    # Format and send response
    if result:
        await update.message.reply_text(f"✅ Hasil dari OLT:\n\n```\n{result}\n```", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Gagal mendapatkan respon dari OLT.")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ends the conversation."""
    await update.message.reply_text("Selesai.")
    return ConversationHandler.END

if __name__ == "__main__":
    if not TOKEN or TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Error: Harap isi TELEGRAM_TOKEN di file .env")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    # Conversation handler for /onu
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("onu", onu_command)],
        states={
            WAITING_FOR_SN: [MessageHandler(filters.TEXT & (~filters.COMMAND), handle_sn)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    print("Bot is running...")
    app.run_polling()
