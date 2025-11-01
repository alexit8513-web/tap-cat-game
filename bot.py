import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import BadRequest

# Токен бота (будет установлен через переменные окружения)
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8288482304:AAHsoKPs4-WfJn2lsQ0scLDto8u3BfCEcvA')

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            score INTEGER DEFAULT 0,
            money INTEGER DEFAULT 100,
            level INTEGER DEFAULT 1,
            click_power INTEGER DEFAULT 1,
            auto_click_power INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Получение пользователя
def get_user(user_id):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        # Создаем нового пользователя
        cursor.execute('''
            INSERT INTO users (user_id, score, money, level, click_power, auto_click_power)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, 0, 100, 1, 1, 0))
        conn.commit()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
    
    conn.close()
    
    return {
        'user_id': user[0],
        'username': user[1],
        'first_name': user[2],
        'score': user[3],
        'money': user[4],
        'level': user[5],
        'click_power': user[6],
        'auto_click_power': user[7],
        'created_at': user[8]
    }

# Обновление данных пользователя
def update_user(user_id, score=None, money=None, level=None, click_power=None, auto_click_power=None):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    
    update_fields = []
    values = []
    
    if score is not None:
        update_fields.append('score = ?')
        values.append(score)
    if money is not None:
        update_fields.append('money = ?')
        values.append(money)
    if level is not None:
        update_fields.append('level = ?')
        values.append(level)
    if click_power is not None:
        update_fields.append('click_power = ?')
        values.append(click_power)
    if auto_click_power is not None:
        update_fields.append('auto_click_power = ?')
        values.append(auto_click_power)
    
    if update_fields:
        values.append(user_id)
        cursor.execute(f'''
            UPDATE users SET {', '.join(update_fields)} WHERE user_id = ?
        ''', values)
    
    conn.commit()
    conn.close()

# Обновление имени пользователя
def update_user_info(user_id, username, first_name):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE users SET username = ?, first_name = ? WHERE user_id = ?
    ''', (username, first_name, user_id))
    
    conn.commit()
    conn.close()

# Получение топа игроков
def get_top_players(limit=10):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_id, username, first_name, score, level 
        FROM users 
        ORDER BY score DESC 
        LIMIT ?
    ''', (limit,))
    
    top_players = cursor.fetchall()
    conn.close()
    
    return top_players

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Получаем или создаем пользователя
    user_data = get_user(user_id)
    
    # Обновляем информацию о пользователе
    update_user_info(user_id, user.username, user.first_name)
    
    # Клавиатура главного меню
    keyboard = [
        [InlineKeyboardButton("🎮 Играть", web_app={'url': 'https://alexit8513-web.github.io/tap-cat-game/'})],
        [InlineKeyboardButton("📊 Моя статистика", callback_data='my_stats')],
        [InlineKeyboardButton("🏆 Топ игроков", callback_data='top_players')],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем приветственное сообщение
    await update.message.reply_text(
        f"Привет, {user.first_name}! 🐱\n\n"
        "Добро пожаловать в Tap Cat Game!\n\n"
        "Тапай по коту, зарабатывай очки и улучшай своего питомца!",
        reply_markup=reply_markup
    )

# Показ статистики пользователя
async def show_my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    try:
        # Получаем данные пользователя
        user = get_user(user_id)
        
        # Форматируем статистику
        stats_text = f"📊 <b>Ваша статистика</b> 🐱\n\n"
        stats_text += f"👤 <b>Игрок:</b> {user['first_name'] or 'Аноним'}\n"
        if user['username']:
            stats_text += f"🔗 <b>Username:</b> @{user['username']}\n"
        stats_text += f"🏆 <b>Очки:</b> {format_number(user['score'])}\n"
        stats_text += f"💰 <b>Деньги:</b> {format_number(user['money'])}\n"
        stats_text += f"🎯 <b>Уровень:</b> {user['level']}\n"
        stats_text += f"💪 <b>Сила клика:</b> {user['click_power']}\n"
        stats_text += f"⚡ <b>Автокликер:</b> {user['auto_click_power']}\n"
        stats_text += f"📅 <b>В игре с:</b> {user['created_at'][:10]}\n\n"
        
        # Расчет прогресса до следующего уровня
        level_requirements = [0, 200, 500, 1000, 2000, 4000, 8000, 15000, 25000, 50000]
        current_level = user['level']
        next_level_score = level_requirements[current_level] if current_level < len(level_requirements) else 0
        
        if next_level_score > 0:
            progress = (user['score'] / next_level_score) * 100
            stats_text += f"📈 <b>Прогресс до уровня {current_level + 1}:</b> {progress:.1f}%\n"
            stats_text += f"🎯 <b>Нужно очков:</b> {format_number(next_level_score - user['score'])}"
        else:
            stats_text += "🎉 <b>Вы достигли максимального уровня!</b>"
        
        # Клавиатура для возврата
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в меню", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            stats_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except BadRequest:
        # Игнорируем ошибку устаревшего запроса
        pass

# Показ топа игроков
async def show_top_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    try:
        # Получаем топ игроков
        top_players = get_top_players(10)
        
        # Форматируем топ
        top_text = "🏆 <b>Топ игроков</b> 🐱\n\n"
        
        if not top_players:
            top_text += "Пока нет игроков в таблице лидеров!\nБудьте первым! 🎮"
        else:
            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            
            for i, player in enumerate(top_players):
                user_id, username, first_name, score, level = player
                medal = medals[i] if i < len(medals) else f"{i+1}."
                
                player_name = first_name or "Аноним"
                if username:
                    player_name = f"@{username}"
                
                top_text += f"{medal} {player_name}\n"
                top_text += f"   🏆 Очки: {format_number(score)} | 🎯 Уровень: {level}\n\n"
        
        # Клавиатура для возврата
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в меню", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            top_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except BadRequest:
        # Игнорируем ошибку устаревшего запроса
        pass

# Показ помощи
async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    try:
        help_text = (
            "ℹ️ <b>Помощь по игре Tap Cat</b> 🐱\n\n"
            "🎮 <b>Как играть:</b>\n"
            "• Тапай по коту для получения очков и денег\n"
            "• Покупай улучшения в магазине\n"
            "• Повышай уровень для бонусов\n"
            "• Автокликер работает автоматически!\n\n"
            
            "🛍️ <b>Улучшения:</b>\n"
            "• 💪 <b>Усилитель</b> - увеличивает силу каждого тапа\n"
            "• ⚡ <b>Автокликер</b> - автоматически зарабатывает очки\n\n"
            
            "📊 <b>Статистика:</b>\n"
            "• Следи за своим прогрессом в разделе 'Моя статистика'\n"
            "• Сравни результаты с другими в 'Топе игроков'\n\n"
            
            "🚀 <b>Советы:</b>\n"
            "• Сначала улучшай усилитель клика\n"
            "• Автокликер полезен на поздних этапах\n"
            "• Регулярно проверяй топ игроков для мотивации!"
        )
        
        # Клавиатура для возврата
        keyboard = [
            [InlineKeyboardButton("🔙 Назад в меню", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    except BadRequest:
        # Игнорируем ошибку устаревшего запроса
        pass

# Возврат в главное меню
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    
    try:
        # Клавиатура главного меню
        keyboard = [
            [InlineKeyboardButton("🎮 Играть", web_app={'url': 'https://alexit8513-web.github.io/tap-cat-game/'})],
            [InlineKeyboardButton("📊 Моя статистика", callback_data='my_stats')],
            [InlineKeyboardButton("🏆 Топ игроков", callback_data='top_players')],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"Главное меню 🐱\n\n"
            "Выберите действие:",
            reply_markup=reply_markup
        )
    except BadRequest:
        # Игнорируем ошибку устаревшего запроса
        pass

# Обработка данных из веб-приложения
async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        web_app_data = update.message.web_app_data
        data = web_app_data.data
        
        # Парсим данные (формат: score=100&money=150&level=2&click_power=3&auto_click_power=1)
        data_dict = {}
        for item in data.split('&'):
            if '=' in item:
                key, value = item.split('=')
                data_dict[key] = value
        
        # Обновляем данные пользователя
        update_user(
            user_id=user_id,
            score=int(data_dict.get('score', 0)),
            money=int(data_dict.get('money', 100)),
            level=int(data_dict.get('level', 1)),
            click_power=int(data_dict.get('click_power', 1)),
            auto_click_power=int(data_dict.get('auto_click_power', 0))
        )
        
        await update.message.reply_text("✅ Прогресс сохранен в базу данных!")
        
    except Exception as e:
        print(f"Ошибка при обработке данных: {e}")
        await update.message.reply_text("❌ Ошибка при сохранении прогресса.")

# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Обновляем информацию о пользователе
    update_user_info(user_id, user.username, user.first_name)
    
    # Показываем главное меню
    keyboard = [
        [InlineKeyboardButton("🎮 Играть", web_app={'url': 'https://alexit8513-web.github.io/tap-cat-game/'})],
        [InlineKeyboardButton("📊 Моя статистика", callback_data='my_stats')],
        [InlineKeyboardButton("🏆 Топ игроков", callback_data='top_players')],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Главное меню 🐱\n\nВыберите действие:",
        reply_markup=reply_markup
    )

# Форматирование больших чисел
def format_number(num):
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    if num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Произошла ошибка: {context.error}")

# Основная функция
def main():
    # Инициализация базы данных
    init_db()
    
    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    application.add_handler(CallbackQueryHandler(show_my_stats, pattern='^my_stats$'))
    application.add_handler(CallbackQueryHandler(show_top_players, pattern='^top_players$'))
    application.add_handler(CallbackQueryHandler(show_help, pattern='^help$'))
    application.add_handler(CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$'))
    
    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запуск бота
    print("🐱 Бот Tap Cat запущен на Render...")
    print("📊 База данных инициализирована")
    print("🎮 Ожидаем сообщения от пользователей...")
    application.run_polling()

if __name__ == '__main__':
    main()