from telegram import Update
from telegram.ext import ContextTypes
import requests
import os
from .utils import (
    is_allowed_user,
    generate_filename,
    ContentType,
    format_content,
    PhotoContentData,
    append_to_note,
    set_reaction
)
from .caption import append_caption
from config import (
    TEMP_FOLDER,
    logger,
)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function for handle photo messege. Add photo and capture to current note"""
    if not is_allowed_user(update):
        return
        
    await set_reaction(update, context)
    
    try:
        photo = update.message.photo[-1]  # Берем фото наилучшего качества
        file = await photo.get_file()
        file_name = generate_filename(ContentType.PHOTO)
        file_path = os.path.join(TEMP_FOLDER, file_name)

        response = requests.get(file.file_path)
        with open(file_path, "wb") as f:
            f.write(response.content)

        # Добавляем фото в заметку
        markdown_link = format_content(ContentType.PHOTO, PhotoContentData(file_name))
        append_caption(update)
        append_to_note(markdown_link)
        await update.message.reply_text(
                "Фото добавлено в заметку. #photo"
            )

    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении фото: {str(e)}")
        logger.error(f"Error in handle_photo: {str(e)}")
