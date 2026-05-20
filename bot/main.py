import logging
import os
import sys
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters
)

from .database import Database
from .handlers import ReminderBotHandlers, WAITING_TEXT, WAITING_DATETIME
from .scheduler import ReminderScheduler

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("ОШИБКА: Не найден TELEGRAM_BOT_TOKEN в файле .env")
    sys.exit(1)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot_app = None
scheduler = None
db = None


async def send_message_to_user(user_id: int, text: str):
    """Callback-функция для отправки сообщения от планировщика."""
    try:
        await bot_app.bot.send_message(chat_id=user_id, text=text)
        logger.info(f"Сообщение отправлено пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")


def main():
    global bot_app, scheduler, db
    
    db = Database("reminders.db")
    logger.info("База данных инициализирована")
    
    handlers = ReminderBotHandlers(db)
    
    bot_app = ApplicationBuilder().token(TOKEN).build()
    
    # Команды
    bot_app.add_handler(CommandHandler("start", handlers.start))
    bot_app.add_handler(CommandHandler("list", handlers.list_reminders))
    bot_app.add_handler(CommandHandler("delete", handlers.delete_reminder))
    bot_app.add_handler(CommandHandler("stats", handlers.stats))
    
    # ConversationHandler для /new
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("new", handlers.new_start)],
        states={
            WAITING_TEXT: [
                CommandHandler("cancel", handlers.cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_text)
            ],
            WAITING_DATETIME: [
                CommandHandler("cancel", handlers.cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.get_datetime)
            ],
        },
        fallbacks=[CommandHandler("cancel", handlers.cancel)]
    )
    bot_app.add_handler(conv_handler)
    bot_app.add_handler(MessageHandler(filters.COMMAND, handlers.unknown))
    
    # Запуск планировщика
    scheduler = ReminderScheduler(db, send_message_to_user)
    scheduler.start()
    
    logger.info("Бот запущен")
    bot_app.run_polling()


if __name__ == "__main__":
    main()
