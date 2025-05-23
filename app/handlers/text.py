from telegram import Update
from telegram.ext import ContextTypes
from config import logger
from .utils import (
    is_allowed_user,
    format_content,
    ContentType,
    TextContentData,
    append_to_note,
    set_reaction
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function for handle text messege. Add text to current note"""
    if not is_allowed_user(update):
        return
    
    await set_reaction(update, context)
    
    try:
        text = update.message.text
        formatted_text = format_content(ContentType.TEXT, TextContentData(text))
        append_to_note(formatted_text)
        await update.message.reply_text("Текст добавлен в заметку.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении текста: {str(e)}")
        logger.error(f"Error in handle_text: {str(e)}")
