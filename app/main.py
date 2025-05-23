import warnings
import asyncio
from telegram import BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from handlers import (
    handle_photo,
    handle_text,
    handle_voice,
    handle_video,
    handle_animation,
    handle_sticker,
    handle_video_note,
    handle_location,
    handle_document
)
from commands import (
    start,
    new_note,
    print_note,
    list_notes,
    delete_note,
    error_handler,
    callback_query,
)
from config import logger, TELEGRAM_TOKEN

# Подавление предупреждения FP16
warnings.filterwarnings("ignore", category=UserWarning)

# Список команд для меню
commands = [
    BotCommand(command="start", description="Запустить бота"),
    BotCommand(command="newnote", description="Создать новую заметку"),
    BotCommand(command="printnote", description="Посмотреть текущую заметку"),
    BotCommand(command="listnotes", description="Показать список заметок"),
    BotCommand(command="deletenote", description="Удалить текущую заметку"),
]


def main():
    """Duty cycle"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newnote", new_note))
    application.add_handler(CommandHandler("printnote", print_note))
    application.add_handler(CommandHandler("listnotes", list_notes))
    application.add_handler(CommandHandler("deletenote", delete_note))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.VIDEO_NOTE, handle_video_note))
    application.add_handler(MessageHandler(filters.ANIMATION, handle_animation))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_error_handler(error_handler)

    # Устанавливаем меню команд асинхронно
    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.bot.set_my_commands(commands))
    logger.info("Меню команд успешно установлено")

    print("Бот запущен...")
    application.add_handler(CallbackQueryHandler(callback_query))
    application.run_polling()


if __name__ == "__main__":
    main()
