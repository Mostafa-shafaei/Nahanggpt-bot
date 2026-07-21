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
        [InlineKeyboardButton(f":whale2: {level_info['name']}", callback_data="show_level")],
        [InlineKeyboardButton(":bar_chart: وضعیت", callback_data="my_status")],
        [InlineKeyboardButton(":gift: دعوت", callback_data="invite")],
        [InlineKeyboardButton(":arrow_up: ارتقاء", callback_data="upgrade_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f":whale: سلام {user.first_name}! من نهنگ هستم.\n"
        f"سطح: {level_info['name']}\n"
        f"مدل: {level_info['model']}\n"
        f"هر پیامی بفرست، پاسخ می‌دهم.\n\n"
        f":ocean: من روی ابر اجرا می‌شوم، پس همیشه بیدارم!",
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
13:51
await query.edit_message_text(
            f":whale: سطح: {level_info['name']}\n"
            f"مدل: {level_info['model']}\n"
            f"محدودیت: {level_info['daily_limit']} پیام در روز"
        )
    elif query.data == "my_status":
        invites = data["invites"].get(user_id, 0)
        usage = load_usage().get(f"{user_id}_{level}_{datetime.now().date()}", 0)
        await query.edit_message_text(
            f":bar_chart: وضعیت شما:\n"
            f"سطح: {level_info['name']}\n"
            f"پیام امروز: {usage}/{level_info['daily_limit']}\n"
            f"دعوت: {invites}"
        )
    elif query.data == "invite":
        code = data["users"].get(user_id, {}).get("invite_code", "")
        await query.edit_message_text(
            f":link: لینک دعوت:\n"
            f"https://t.me/{(await context.bot.get_me()).username}?start={code}\n\n"
            f"۲ دعوت → دلفین | ۵ → وال | ۱۰ → نهنگ آبی"
        )
    elif query.data == "upgrade_info":
        await query.edit_message_text(
            ":arrow_up: ارتقاء با دعوت:\n"
            ":dolphin: دلفین: ۲ دعوت\n"
            ":whale2: وال: ۵ دعوت\n"
            ":whale: نهنگ آبی: ۱۰ دعوت"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_msg = update.message.text
    if not user_msg or user_msg.startswith("/"):
        return
    
    level = get_user_level(user_id)
    msg = await update.message.reply_text(":whale: نهنگ در حال فکر کردن...")
    
    try:
        response = await call_ai_api(level, user_msg)
        await msg.edit_text(f":whale2: {LEVELS[level]['name']}:\n\n{response[:3000]}")
    except Exception as e:
        logger.error(e)
        await msg.edit_text(":x: خطا. دوباره تلاش کن.")

# ==================== اجرا ====================
def main():
    if not TOKEN or TOKEN == "YOUR_BOT_TOKEN":
        logger.error(":x: توکن تنظیم نشده! متغیر TOKEN را بگذار.")
        sys.exit(1)
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info(":whale: نهنگ به آب انداخته شد — همیشه بیدار!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if name == "main":
    main()
    
