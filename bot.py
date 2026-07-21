#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات نهنگ (WHALE) — نسخه‌ی ابری با ۴ سطح هوش مصنوعی
همیشه فعال، حتی وقتی لپ‌تاپ خاموش است
"""

import asyncio
import json
import logging
import os
import random
import sys
from datetime import datetime
from pathlib import Path

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ==================== تنظیمات از محیط ====================
TOKEN = os.environ.get("TOKEN", "YOUR_BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789))

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ==================== داده‌ها ====================
DATA_FILE = Path("whale_data.json")
USAGE_FILE = Path("whale_usage.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ==================== سیستم ۴ سطح ====================
LEVELS = {
    "free": {
        "name": "🐟 کریل",
        "daily_limit": 20,
        "model": "gpt-3.5-turbo",
        "api": "openai",
        "prompt": "شما یک دستیار ساده هستید."
    },
    "plus": {
        "name": "🐬 دلفین",
        "daily_limit": 60,
        "model": "gemini-1.5-flash",
        "api": "gemini",
        "prompt": "شما یک دستیار حرفه‌ای هستید."
    },
    "pro": {
        "name": "🐋 وال",
        "daily_limit": 50,
        "model": "claude-3-haiku-20240307",
        "api": "claude",
        "prompt": "شما یک کارشناس ارشد هستید."
    },
    "premium": {
        "name": "🐳 نهنگ آبی",
        "daily_limit": 30,
        "model": "llama3-70b-8192",
        "api": "groq",
        "prompt": "شما یک هوش فرازمینی هستید."
    }
}

# ==================== توابع داده ====================
def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "invites": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_usage():
    if USAGE_FILE.exists():
        with open(USAGE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_usage(usage):
    with open(USAGE_FILE, "w") as f:
        json.dump(usage, f, indent=2)

def get_user_level(user_id):
    data = load_data()
    user = data["users"].get(user_id, {})
    invites = data["invites"].get(user_id, 0)
    if invites >= 10:
        return "premium"
    elif invites >= 5:
        return "pro"
    elif invites >= 2:
        return "plus"
    return user.get("level", "free")

# ==================== APIها ====================
async def call_ai_api(level, user_msg):
    config = LEVELS[level]
    api_type = config["api"]
    model = config["model"]
    sys_prompt = config["prompt"]
    
    try:
        if api_type == "openai" and OPENAI_API_KEY:
            return await call_openai(model, sys_prompt, user_msg)
        elif api_type == "gemini" and GEMINI_API_KEY:
            return await call_gemini(model, sys_prompt, user_msg)
        elif api_type == "claude" and CLAUDE_API_KEY:
            return await call_claude(model, sys_prompt, user_msg)
        elif api_type == "groq" and GROQ_API_KEY:
            return await call_groq(model, sys_prompt, user_msg)
        else:
            return "⚠️ کلید API تنظیم نشده. از /start استفاده کن."
    except Exception as e:
        logger.error(f"API error: {e}")
        return "❌ خطا در ارتباط. بعداً امتحان کن."

async def call_openai(model, sys_prompt, user_msg):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}],
        "temperature": 0.7,
        "max_tokens": 500
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

async def call_gemini(model, sys_prompt, user_msg):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": f"{sys_prompt}\n\nکاربر: {user_msg}"}]}]}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

async def call_claude(model, sys_prompt, user_msg):
    url = "https://api.anthropic.com/v1/messages"
    headers = {"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
    payload = {"model": model, "system": sys_prompt, "messages": [{"role": "user", "content": user_msg}], "max_tokens": 500}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            data = await resp.json()
            return data["content"][0]["text"]

async def call_groq(model, sys_prompt, user_msg):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_msg}],
        "temperature": 0.8,
        "max_tokens": 600
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

# ==================== دستورات ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    data = load_data()
    
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "first_name": user.first_name,
            "username": user.username,
            "joined": datetime.now().isoformat(),
            "level": "free",
            "invite_code": f"whale_{user_id}_{random.randint(1000,9999)}"
        }
        save_data(data)
    
    level = get_user_level(user_id)
    level_info = LEVELS[level]
    
    keyboard = [
        [InlineKeyboardButton(f"🐋 {level_info['name']}", callback_data="show_level")],
        [InlineKeyboardButton("📊 وضعیت", callback_data="my_status")],
        [InlineKeyboardButton("🎁 دعوت", callback_data="invite")],
        [InlineKeyboardButton("⬆️ ارتقاء", callback_data="upgrade_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🐳 سلام {user.first_name}! من **نهنگ** هستم.\n"
        f"سطح: {level_info['name']}\n"
        f"مدل: {level_info['model']}\n"
        f"هر پیامی بفرست، پاسخ می‌دهم.\n\n"
        f"🌊 من روی ابر اجرا می‌شوم، پس همیشه بیدارم!",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    level = get_user_level(user_id)
    level_info = LEVELS[level]
    data = load_data()
    
    if query.data == "show_level":
        await query.edit_message_text(
            f"🐳 سطح: {level_info['name']}\n"
            f"مدل: {level_info['model']}\n"
            f"محدودیت: {level_info['daily_limit']} پیام در روز"
        )
    elif query.data == "my_status":
        invites = data["invites"].get(user_id, 0)
        usage = load_usage().get(f"{user_id}_{level}_{datetime.now().date()}", 0)
        await query.edit_message_text(
            f"📊 وضعیت شما:\n"
            f"سطح: {level_info['name']}\n"
            f"پیام امروز: {usage}/{level_info['daily_limit']}\n"
            f"دعوت: {invites}"
        )
    elif query.data == "invite":
        code = data["users"].get(user_id, {}).get("invite_code", "")
        await query.edit_message_text(
            f"🔗 لینک دعوت:\n"
            f"https://t.me/{(await context.bot.get_me()).username}?start={code}\n\n"
            f"۲ دعوت → دلفین | ۵ → وال | ۱۰ → نهنگ آبی"
        )
    elif query.data == "upgrade_info":
        await query.edit_message_text(
            "⬆️ ارتقاء با دعوت:\n"
            "🐬 دلفین: ۲ دعوت\n"
            "🐋 وال: ۵ دعوت\n"
            "🐳 نهنگ آبی: ۱۰ دعوت"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_msg = update.message.text
    if not user_msg or user_msg.startswith("/"):
        return
    
    level = get_user_level(user_id)
    msg = await update.message.reply_text("🐳 نهنگ در حال فکر کردن...")
    
    try:
        response = await call_ai_api(level, user_msg)
        await msg.edit_text(f"🐋 {LEVELS[level]['name']}:\n\n{response[:3000]}")
    except Exception as e:
        logger.error(e)
        await msg.edit_text("❌ خطا. دوباره تلاش کن.")

# ==================== اجرا ====================
def main():
    if not TOKEN or TOKEN == "YOUR_BOT_TOKEN":
        logger.error("❌ توکن تنظیم نشده! متغیر TOKEN را بگذار.")
        sys.exit(1)
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🐳 نهنگ به آب انداخته شد — همیشه بیدار!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
