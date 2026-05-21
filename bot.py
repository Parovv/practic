import threading
import time
from datetime import datetime
import re
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from config import TOKEN
import db_handler
import analyzer

bot = telebot.TeleBot(TOKEN)


user_states = {}



def main_menu_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("➕ Записать день"), KeyboardButton("📊 Статистика"))
    markup.add(KeyboardButton("📜 История"), KeyboardButton("⚙️ Настройки"))
    markup.add(KeyboardButton("🗑 Очистить данные"))
    return markup

def mood_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("1 😞", callback_data="mood_1"),
        InlineKeyboardButton("2 😐", callback_data="mood_2"),
        InlineKeyboardButton("3 🙂", callback_data="mood_3"),
        InlineKeyboardButton("4 😊", callback_data="mood_4"),
        InlineKeyboardButton("5 🤩", callback_data="mood_5")
    )
    return markup

def hours_keyboard(prefix):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("0.5 ч", callback_data=f"{prefix}_0.5"),
        InlineKeyboardButton("1 ч", callback_data=f"{prefix}_1"),
        InlineKeyboardButton("2 ч", callback_data=f"{prefix}_2"),
        InlineKeyboardButton("4 ч", callback_data=f"{prefix}_4"),
        InlineKeyboardButton("Другое...", callback_data=f"{prefix}_custom")
    )
    return markup

def stats_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📅 За неделю", callback_data="stats_7"),
        InlineKeyboardButton("🗓 За месяц", callback_data="stats_30")
    )
    markup.add(
        InlineKeyboardButton("🔍 Мои инсайты", callback_data="stats_insights"),
        InlineKeyboardButton("📉 График", callback_data="stats_graph")
    )
    return markup

def confirm_clear_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Да, удалить", callback_data="clear_yes"),
        InlineKeyboardButton("❌ Отмена", callback_data="clear_no")
    )
    return markup

def settings_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("18:00", callback_data="time_18:00"),
        InlineKeyboardButton("21:00", callback_data="time_21:00"),
        InlineKeyboardButton("23:00", callback_data="time_23:00")
    )
    markup.add(InlineKeyboardButton("✍️ Ввести вручную", callback_data="time_custom"))
    return markup



@bot.message_handler(commands=['start'])
def start(message):
    db_handler.add_user(message.chat.id, message.from_user.username)
    text = (
        "Привет! 👋 Я трекер настроения и продуктивности.\n\n"
        "Я помогу тебе отслеживать, как сон и работа влияют на твое самочувствие. "
        "Просто записывай свои данные каждый день, а я найду скрытые закономерности!\n\n"
        "Нажми «➕ Записать день», чтобы начать."
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu_keyboard())

@bot.message_handler(commands=['help'])
def help_command(message):
    text = (
      "/start - Запуск бота\n"
      "/add - Записать день\n"
      "/stats - Статистика\n"
      "/history - История записей\n"
      "/settings - Настройки времени\n"
      "/clear - Очистить данные"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['add'])
@bot.message_handler(func=lambda m: m.text == "➕ Записать день")
def add_record_start(message):
    user_states[message.chat.id] = {'step': 'mood', 'data': {}}
    bot.send_message(message.chat.id, "Оцени свое настроение сегодня от 1 до 5, где 1 — ужасно, 5 — отлично.", reply_markup=mood_keyboard())

@bot.message_handler(commands=['stats'])
@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stats_menu(message):
    bot.send_message(message.chat.id, "Что хочешь узнать?", reply_markup=stats_keyboard())

@bot.message_handler(commands=['history'])
@bot.message_handler(func=lambda m: m.text == "📜 История")
def show_history(message):
    data = db_handler.get_history(message.chat.id)
    if not data:
        bot.send_message(message.chat.id, "История пуста. Начни записывать свои дни!")
        return
    
    response = "📜 Последние записи:\n\n"
    for row in data:
        response += (f"📅 {row['record_date']}\n"
                     f"  😊 Настроение: {row['mood']}\n"
                     f"  💻 Работа: {row['work_hours']} ч\n"
                     f"  🛏 Сон: {row['sleep_hours']} ч\n")
        if row['comment']:
            response += f"  💬 {row['comment']}\n"
        response += "\n"
    
    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['settings'])
@bot.message_handler(func=lambda m: m.text == "⚙️ Настройки")
def settings_menu(message):
    current_time = db_handler.get_reminder_time(message.chat.id)
    bot.send_message(message.chat.id, f"Текущее время напоминания: {current_time}\nВыбери новое:", reply_markup=settings_keyboard())

@bot.message_handler(commands=['clear'])
@bot.message_handler(func=lambda m: m.text == "🗑 Очистить данные")
def clear_data_ask(message):
    bot.send_message(message.chat.id, "⚠️ Ты уверен, что хочешь удалить ВСЕ свои данные? Это нельзя отменить.", reply_markup=confirm_clear_keyboard())



@bot.callback_query_handler(func=lambda call: call.data.startswith('mood_'))
def handle_mood(call):
    mood = int(call.data.split('_')[1])
    user_states[call.message.chat.id] = {'step': 'work', 'data': {'mood': mood}}
    bot.edit_message_text(f"Настроение: {mood} принято!", call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "Сколько часов ты потратил на полезную работу/учебу?", reply_markup=hours_keyboard("work"))

@bot.callback_query_handler(func=lambda call: call.data.startswith('work_'))
def handle_work(call):
    chat_id = call.message.chat.id
    state = user_states.get(chat_id)
    if not state or state['step'] != 'work': return
    
    data = call.data.split('_')[1]
    
    if data == "custom":
        state['step'] = 'awaiting_work_input'
        bot.edit_message_text("Введи количество часов работы/учебы (например, 3.5):", chat_id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_custom_work)
    else:
        state['data']['work_hours'] = float(data)
        state['step'] = 'sleep'
        bot.edit_message_text(f"Работа: {data} ч принята!", chat_id, call.message.message_id)
        bot.send_message(chat_id, "Сколько часов ты спал?", reply_markup=hours_keyboard("sleep"))

def process_custom_work(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    try:
        hours = float(message.text)
        state['data']['work_hours'] = hours
        state['step'] = 'sleep'
        bot.send_message(chat_id, f"Работа: {hours} ч принята!\nСколько часов ты спал?", reply_markup=hours_keyboard("sleep"))
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введи число (например, 2.5). Попробуй снова:")
        bot.register_next_step_handler(message, process_custom_work)

@bot.callback_query_handler(func=lambda call: call.data.startswith('sleep_'))
def handle_sleep(call):
    chat_id = call.message.chat.id
    state = user_states.get(chat_id)
    if not state or state['step'] != 'sleep': return
    
    data = call.data.split('_')[1]
    
    if data == "custom":
        state['step'] = 'awaiting_sleep_input'
        bot.edit_message_text("Введи количество часов сна (например, 7.5):", chat_id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_custom_sleep)
    else:
        state['data']['sleep_hours'] = float(data)
        bot.edit_message_text(f"Сон: {data} ч принят!", chat_id, call.message.message_id)
        ask_comment(chat_id)

def process_custom_sleep(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    try:
        hours = float(message.text.replace(',', '.'))
        state['data']['sleep_hours'] = hours
        bot.send_message(chat_id, f"🛏 Сон: {hours} ч принят!")
        ask_comment(chat_id)
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введи число (например, 7.5). Попробуй снова:")
        bot.register_next_step_handler(message, process_custom_sleep)


def send_reminders():
    while True:
        now = datetime.now()
        
        if now.second < 5:
            current_time = now.strftime("%H:%M")
            users = db_handler.get_users_for_reminder(current_time)
            
            for user_id in users:
                
                if not db_handler.has_record_today(user_id):
                    try:
                        bot.send_message(
                            user_id,
                            "⏰ Привет! Напоминаю, что еще не записал свои показатели за сегодня. Нажми «➕ Записать день»!",
                            reply_markup=main_menu_keyboard()
                        )
                    except Exception as e:
                        print(f"Не удалось отправить напоминание пользователю {user_id}: {e}")
            
        
        time.sleep(10)

def start_reminder_thread():
    
    thread = threading.Thread(target=send_reminders, daemon=True)
    thread.start()

def ask_comment(chat_id):
    state = user_states.get(chat_id)
    state['step'] = 'comment'
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Пропустить", callback_data="comment_skip"))
    bot.send_message(chat_id, "Хочешь добавить комментарий? (Напиши текст или нажми «Пропустить»)", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'comment_skip')
def finish_record(call):
    save_record(call.message.chat.id, None)

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'comment')
def handle_text_comment(message):
    save_record(message.chat.id, message.text)

def save_record(chat_id, comment):
    state = user_states.pop(chat_id, None)
    if not state: return
    
    d = state['data']
    db_handler.add_record(chat_id, d.get('mood'), d.get('work_hours'), d.get('sleep_hours'), comment)
    bot.send_message(chat_id, "✅ Запись успешно сохранена! Молодец, что следишь за собой.", reply_markup=main_menu_keyboard())



@bot.callback_query_handler(func=lambda call: call.data.startswith('stats_'))
def handle_stats(call):
    chat_id = call.message.chat.id
    action = call.data.split('_')[1]
    
    if action in ['7', '30']:
        days = int(action)
        data = db_handler.get_stats(chat_id, days)
        text = analyzer.calculate_averages(data)
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode='HTML')
        
    elif action == 'insights':
        data = db_handler.get_stats(chat_id, 30)
        text = analyzer.generate_insights(data)
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode='HTML')
        
    elif action == 'graph':
        data = db_handler.get_stats(chat_id, 30)
        if not data:
            bot.edit_message_text("Нет данных для графика.", chat_id, call.message.message_id)
            return
        buf = analyzer.generate_plot(data)
        if buf:
            bot.delete_message(chat_id, call.message.message_id)
            bot.send_photo(chat_id, buf, caption="📉 Твои показатели за последние 30 дней")
        else:
            bot.edit_message_text("Не удалось построить график.", chat_id, call.message.message_id)



@bot.callback_query_handler(func=lambda call: call.data.startswith('time_'))
def handle_time_settings(call):
    chat_id = call.message.chat.id
    data = call.data

    
    if data == "time_custom":
        msg = bot.send_message(
            chat_id,
            "Введите время напоминания в формате HH:MM (например 07:30 или 21:05)."
        )
        bot.register_next_step_handler(msg, process_custom_time)
        return

    
    time_str = data.split('time_', 1)[1]
    db_handler.set_reminder_time(chat_id, time_str)
    bot.edit_message_text(
        f"✅ Время напоминания установлено на {time_str}",
        chat_id,
        call.message.message_id
    )



    

def normalize_time_str(t: str) -> str:
    
    t = t.strip()
    parts = t.split(':')
    h = int(parts[0])
    m = int(parts[1])
    return f"{h:02d}:{m:02d}"

def is_valid_time(t: str) -> bool:
    return re.fullmatch(r"\d{2}:\d{2}", t) is not None

def process_custom_time(message):
    chat_id = message.chat.id
    raw = message.text

    try:
        norm = normalize_time_str(raw)
    except Exception:
        bot.send_message(chat_id, "❌ Неверный формат. Пример: 14:00")
        return

    if not is_valid_time(norm):
        bot.send_message(chat_id, "❌ Неверный формат. Пример: 14:00")
        return

    hh, mm = norm.split(':')
    hh_i, mm_i = int(hh), int(mm)
    if not (0 <= hh_i <= 23 and 0 <= mm_i <= 59):
        bot.send_message(chat_id, "❌ Часы/минуты вне диапазона. Пример: 14:00")
        return

    db_handler.set_reminder_time(chat_id, norm)
    bot.send_message(chat_id, f"✅ Время напоминания установлено на {norm}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('clear_'))
def handle_clear(call):
    chat_id = call.message.chat.id
    if call.data == 'clear_yes':
        db_handler.clear_data(chat_id)
        bot.edit_message_text("🗑 Все твои данные были удалены.", chat_id, call.message.message_id)
    else:
        bot.edit_message_text("❌ Отменено. Данные в безопасности.", chat_id, call.message.message_id)



if __name__ == '__main__':
    print("Инициализация БД...")
    db_handler.init_db()
    
    
    commands = [
        BotCommand('start', 'Запуск бота, приветствие и инструкция'),
        BotCommand('add', 'Записать день'),
        BotCommand('stats', 'Показ сводки за неделю/месяц'),
        BotCommand('help', 'Краткая справка'),
        BotCommand('history', 'История записей'),
        BotCommand('settings', 'Настройки (изменение времени напоминаний)'),
        BotCommand('clear', 'Очистка данных при подтверждении')
    ]
    bot.set_my_commands(commands)
    
    
    start_reminder_thread()
    
    print("Бот запущен!")
    bot.polling()