from telegram import Update
from telegram.ext import (
    ContextTypes,
)
import requests
import os

from config import (
    TEMP_FOLDER,
    logger,
)
from .utils import (
    is_allowed_user,
    append_to_note,
    generate_filename,
    format_content,
    TextContentData,
    ContentType,
    StickerContentData,
)


async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function to handle sticker message. Add sticker image to current note"""
    if not is_allowed_user(update):
        return
    try:
        sticker = update.message.sticker
        file = await sticker.get_file()
        file_name = generate_filename(ContentType.STICKER, update)  # Передаем update
        file_path = os.path.join(TEMP_FOLDER, file_name)

        response = requests.get(file.file_path)
        with open(file_path, "wb") as f:
            f.write(response.content)

        # Добавляем стикер в заметку
        markdown_link = format_content(
            ContentType.STICKER, StickerContentData(file_name)
        )
        append_to_note(markdown_link)

        # Проверяем, есть ли подпись к стикеру
        caption = update.message.caption
        if caption:
            formatted_caption = format_content(
                ContentType.CAPTION, TextContentData(caption)
            )
            append_to_note(formatted_caption)
            await update.message.reply_text(
                "Стикер и подпись добавлены в заметку. #sticker"
            )
        else:
            await update.message.reply_text("Стикер добавлен в заметку. #sticker")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении стикера: {str(e)}")
        logger.error(f"Error in handle_sticker: {str(e)}")
