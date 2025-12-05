
# bot.py
import telebot
from telebot import types
from config import BOT_TOKEN, MODERATOR_IDS
from database import init_db, get_user, create_user, get_tickets, get_top_users, create_submission

bot = telebot.TeleBot(BOT_TOKEN)
init_db()

# --- Основное меню ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎟 Мои тикеты", "📊 Рейтинг")
    markup.add("➕ Получить тикеты", "🎁 Призы")
    return markup

# --- Старт ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user{user_id}"
    display_name = message.from_user.first_name or username

    if not get_user(user_id):
        create_user(user_id, username, display_name)
        bot.send_message(
            message.chat.id,
            f"🎄 Добро пожаловать, {display_name}!\n\n"
            "Ты участвуешь в новогоднем конкурсе «Билет в удачу»!\n"
            "Собирай тикеты за задания — побеждает тот, у кого их больше всего.",
            reply_markup=main_menu()
        )
    else:
        bot.send_message(
            message.chat.id,
            "С возвращением! Продолжай собирать тикеты 🎟",
            reply_markup=main_menu()
        )

# --- Главные кнопки ---
@bot.message_handler(func=lambda m: m.text == "🎟 Мои тикеты")
def show_tickets(message):
    tickets = get_tickets(message.from_user.id)
    bot.send_message(message.chat.id, f"🎫 У тебя {tickets} тикетов!")

@bot.message_handler(func=lambda m: m.text == "📊 Рейтинг")
def show_rating(message):
    top = get_top_users(10)
    text = "🏆 ТОП-10 участников:\n\n"
    for i, (name, score) in enumerate(top, 1):
        text += f"{i}. {name} — {score} 🎟\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "🎁 Призы")
def show_prizes(message):
    bot.send_message(
        message.chat.id,
        "🎁 Главный приз: AirPods Pro\n"
        "2–5 места: брендовые кружки и мерч\n"
        "Специальные номинации — за креатив и активность!\n\n"
        "Конкурс завершится 30 декабря 2025 в 23:59."
    )

# --- Получить тикеты ---
@bot.message_handler(func=lambda m: m.text == "➕ Получить тикеты")
def get_tickets_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📸 Репост / Скриншот", callback_data="task:screenshot"))
    markup.add(types.InlineKeyboardButton("🎥 Короткое видео", callback_data="task:video"))
    markup.add(types.InlineKeyboardButton("☕ QR с кофе", callback_data="task:qr_info"))
    markup.add(types.InlineKeyboardButton("📅 Ежедневное задание", callback_data="task:daily"))
    bot.send_message(message.chat.id, "Выбери, за что хочешь получить тикеты:", reply_markup=markup)

# --- Обработка кнопок ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("task:"))
def handle_task(call):
    bot.answer_callback_query(call.id)
    task = call.data.split(":")[1]

    if task == "screenshot":
        bot.send_message(call.message.chat.id, "Пришлите скриншот репоста или подписки. Обязательно укажите, за что тикеты (например: «репост в сторис»).")
        bot.register_next_step_handler(call.message, receive_screenshot)
    elif task == "video":
        bot.send_message(call.message.chat.id, "Пришлите ссылку на ваш TikTok, YouTube Shorts, Reels или VK Clip с хештегом #БилетВУдачу2025.")
        bot.register_next_step_handler(call.message, receive_video)
    elif task == "qr_info":
        bot.send_message(call.message.chat.id, "Купите новогоднее кофе в партнёрской точке и отсканируйте QR-код на стаканчике — он приведёт вас сюда автоматически!\n\n(Эта функция активируется при переходе по QR.)")
    elif task == "daily":
        bot.send_message(call.message.chat.id, "Сегодняшнее задание:\n«Сфотографируйте свой новогодний носок 🧦»\n\nПришлите фото!")
        bot.register_next_step_handler(call.message, receive_daily)

# --- Приём контента ---
def receive_screenshot(message):
    if message.content_type in ['photo', 'document']:
        file_id = message.photo[-1].file_id if message.photo else message.document.file_id
        submission_id = create_submission(message.from_user.id, "screenshot", file_id)
        forward_to_moderators(message, "скриншот/репост", submission_id)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, пришлите изображение.")

def receive_video(message):
    if message.text and (message.text.startswith('http') or 'tiktok' in message.text or 'youtube' in message.text):
        submission_id = create_submission(message.from_user.id, "video", message.text)
        forward_to_moderators(message, "видео", submission_id)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, пришлите корректную ссылку.")

def receive_daily(message):
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        submission_id = create_submission(message.from_user.id, "daily", file_id)
        forward_to_moderators(message, "ежедневное задание", submission_id)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, пришлите фото.")

def forward_to_moderators(message, task_name, submission_id):
    caption = f"🔔 Новая заявка на тикеты!\n\nТип: {task_name}\nОт: @{message.from_user.username} (ID: {message.from_user.id})"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ +3", callback_data=f"approve:{submission_id}:3"),
        types.InlineKeyboardButton("✅ +5", callback_data=f"approve:{submission_id}:5"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject:{submission_id}")
    )
    for mod_id in MODERATOR_IDS:
        try:
            if message.content_type == 'photo':
                bot.send_photo(mod_id, message.photo[-1].file_id, caption=caption, reply_markup=markup)
            elif message.content_type == 'text':
                bot.send_message(mod_id, caption + f"\nСсылка: {message.text}", reply_markup=markup)
            else:
                bot.send_message(mod_id, caption, reply_markup=markup)
        except:
            pass  # модератор не активен
    bot.send_message(message.chat.id, "✅ Заявка отправлена на модерацию! Результат пришлют позже.")

# --- Модерация ---
@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve:", "reject:")))
def handle_moderation(call):
    bot.answer_callback_query(call.id)
    parts = call.data.split(":")
    action = parts[0]
    submission_id = int(parts[1])

    if action == "approve":
        tickets = int(parts[2])
        from database import approve_submission
        approve_submission(submission_id, tickets)
        # Уведомить пользователя
        conn = sqlite3.connect('lucky.db')
        cur = conn.cursor()
        cur.execute('SELECT user_id FROM submissions WHERE id = ?', (submission_id,))
        user_id = cur.fetchone()[0]
        conn.close()
        try:
            bot.send_message(user_id, f"🎉 Ваша заявка одобрена! Вам начислено {tickets} тикетов.")
        except:
            pass
        bot.edit_message_caption("✅ Одобрено", call.message.chat.id, call.message.message_id)
    elif action == "reject":
        bot.edit_message_caption("❌ Отклонено", call.message.chat.id, call.message.message_id)

# --- Обработка QR-кодов (через /start=coffee_xxx) ---
@bot.message_handler(commands=['start'])
def handle_start_with_param(message):
    # telebot не даёт напрямую получить параметр, но можно так:
    text = message.text
    if text.startswith('/start coffee_'):
        user_id = message.from_user.id
        if not get_user(user_id):
            username = message.from_user.username or f"user{user_id}"
            display_name = message.from_user.first_name or username
            create_user(user_id, username, display_name)
        from database import add_tickets
        add_tickets(user_id, 3)
        bot.send_message(
            message.chat.id,
            "☕ Вы отсканировали QR с новогодним кофе!\n🎟 +3 тикета начислено.\n\nТеперь украсьте ёлку в боте — и получите ещё +1! 🎄",
            reply_markup=main_menu()
        )
    else:
        send_welcome(message)  # обычный /start

# --- Запуск ---
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()