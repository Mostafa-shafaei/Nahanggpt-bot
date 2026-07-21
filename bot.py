#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات نهنگ (WHALE) — نسخه‌ی ساده و کاملاً سازگار با Render
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==================== تنظیمات ====================
TOKEN = os.environ.get("TOKEN", "YOUR_BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==================== دستورات ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🐳 درباره نهنگ", callback_data="about")],
        [InlineKeyboardButton("📊 وضعیت", callback_data="status")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🐳 سلام {user.first_name}! من **نهنگ** هستم.\n"
        f"یک ربات ساده اما قدرتمند.\n"
        f"برای شروع، یک دکمه را بزن:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "about":
        await query.edit_message_text(
            "🐋 من نهنگ هستم، رباتی که توسط CAT ساخته شده.\n"
            "هدفم کمک به شماست، هر سوالی دارید بپرسید."
        )
    elif query.data == "status":
        await query.edit_message_text(
            "✅ ربات فعال است!\n"
            f"🆔 ادمین: {ADMIN_ID}\n"
            "🌊 من روی Render اجرا می‌شوم."
        )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and not update.message.text.startswith("/"):
        await update.message.reply_text(
            f"🐳 شما گفتید: {update.message.text}\n"
            f"من نهنگ هستم و پیامتان را دریافت کردم!"
        )

# ==================== اجرا ====================
def main():
    if not TOKEN or TOKEN == "YOUR_BOT_TOKEN":
        logger.error("❌ توکن تنظیم نشده!")
        return
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    logger.info("🐳 نهنگ روشن شد!")
    app.run_polling()

if __name__ == "__main__":
    main()
