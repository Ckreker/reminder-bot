import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from .database import Database
from .utils import parse_datetime, format_reminder_time

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_TEXT = 1
WAITING_DATETIME = 2


class ReminderBotHandlers:
    """Класс с обработчиками команд бота."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start."""
        await update.message.reply_text(
            "Привет! Я бот-напоминалка.\n\n"
            "Команды:\n"
            "/new - создать новое напоминание\n"
            "/list - показать мои напоминания\n"
            "/delete <id> - удалить напоминание\n"
            "/stats - статистика\n"
            "/cancel - отменить создание\n\n"
            "Форматы даты:\n"
            "• 2025-12-31 18:00\n"
            "• завтра 15:30\n"
            "• через 2 часа\n"
            "• через 30 минут",
            parse_mode="Markdown"
        )
    
    async def new_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало создания напоминания (шаг 1 - текст)."""
        await update.message.reply_text(
            "Введите текст напоминания\n\nДля отмены введите /cancel",
            parse_mode="Markdown"
        )
        return WAITING_TEXT
    
    async def get_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Шаг 2 - получаем текст, запрашиваем дату."""
        context.user_data['reminder_text'] = update.message.text
        
        await update.message.reply_text(
            "Введите дату и время напоминания\n\n"
            "• 2025-12-31 18:00\n"
            "• завтра 15:30\n"
            "• через 2 часа\n"
            "• через 30 минут\n\n"
            "Для отмены введите /cancel",
            parse_mode="Markdown"
        )
        return WAITING_DATETIME
    
    async def get_datetime(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Шаг 3 - парсим дату и сохраняем напоминание."""
        user_id = update.effective_user.id
        text = context.user_data['reminder_text']
        datetime_str = update.message.text
        
        remind_time = parse_datetime(datetime_str)
        
        if remind_time is None:
            await update.message.reply_text(
                "Неверный формат даты! Попробуйте снова или введите /cancel",
                parse_mode="Markdown"
            )
            return WAITING_DATETIME
        
        if remind_time < datetime.now():
            await update.message.reply_text(
                "Нельзя установить напоминание в прошлом!",
                parse_mode="Markdown"
            )
            return WAITING_DATETIME
        
        reminder_id = self.db.add_reminder(user_id, text, remind_time)
        
        await update.message.reply_text(
            f"Напоминание создано!\n\n"
            f"Текст: `{text}`\n"
            f"Время: {format_reminder_time(remind_time)}\n"
            f"ID: `{reminder_id}`",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    async def list_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список активных напоминаний."""
        user_id = update.effective_user.id
        reminders = self.db.get_active_reminders(user_id)
        
        if not reminders:
            await update.message.reply_text("У вас нет активных напоминаний.")
            return
        
        message = "ВАШИ НАПОМИНАНИЯ:\n\n"
        for rem_id, text, time_str in reminders:
            time_obj = datetime.fromisoformat(time_str)
            message += f"ID `{rem_id}` | {format_reminder_time(time_obj)}\n"
            message += f"   {text}\n\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def delete_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить напоминание по ID: /delete 123"""
        try:
            reminder_id = int(context.args[0])
        except (IndexError, ValueError):
            await update.message.reply_text(
                "Использование: `/delete <id>`\nПример: `/delete 5`",
                parse_mode="Markdown"
            )
            return
        
        user_id = update.effective_user.id
        success = self.db.delete_reminder(reminder_id, user_id)
        
        if success:
            await update.message.reply_text(f"Напоминание {reminder_id} удалено.")
        else:
            await update.message.reply_text(f"Напоминание {reminder_id} не найдено.")
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать статистику пользователя."""
        user_id = update.effective_user.id
        count = self.db.get_reminder_count(user_id)
        
        await update.message.reply_text(
            f"Ваша статистика\n\nАктивных напоминаний: `{count}`",
            parse_mode="Markdown"
        )
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отменить создание напоминания."""
        await update.message.reply_text("Создание напоминания отменено.")
        return ConversationHandler.END
    
    async def unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик неизвестных команд."""
        await update.message.reply_text("Неизвестная команда. Используйте /start")
