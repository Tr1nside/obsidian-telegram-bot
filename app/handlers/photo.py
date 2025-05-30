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
    main_decorator,
)
from .caption import append_caption
from config import (
    TEMP_FOLDER,
    logger,
)


@main_decorator
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function for handle photo messege. Add photo and capture to current note"""
    if not is_allowed_user(update):
        return

    try:
        photo = update.message.photo[-1]  # Берем фото наилучшего качества
        file = await photo.get_file()
        file_name = generate_filename(ContentType.PHOTO)
        file_path = os.path.join(TEMP_FOLDER, file_name)
        if not file_path:
            await update.message.reply_text("Ошибка при добавлении фото: не указан путь к файлу")
            logger.error("Ошибка при добавлении фото: не указан путь к файлу")  
            return  
        
        response = requests.get(file.file_path)
        if not response.content:
            await update.message.reply_text("Не удалось загрузить фото.")
            logger.error("Response content is empty")
            return
        
        with open(file_path, "wb") as f:
            f.write(response.content)

        # Добавляем фото в заметку
        markdown_link = format_content(ContentType.PHOTO, PhotoContentData(file_name))
        append_caption(update)

        append_to_note(markdown_link)
        
        await update.message.reply_text("Фото добавлено в заметку. #photo")

    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении фото: {str(e)}")
        logger.error(f"Error in handle_photo: {str(e)}")
