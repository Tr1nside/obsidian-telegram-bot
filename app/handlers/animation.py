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
    AnimationContentData,
    BigMediaData,
    ContentType,
)


async def handle_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function for handle gif messege. Add gif and capture to current note"""
    if not is_allowed_user(update):
        return
    try:
        animation = update.message.animation

        if animation.file_size < 52428800:
            file = await animation.get_file()
            file_name = generate_filename(ContentType.ANIMATION)
            file_path = os.path.join(TEMP_FOLDER, file_name)

            response = requests.get(file.file_path)
            with open(file_path, "wb") as f:
                f.write(response.content)

            # Добавляем фото в заметку
            markdown_link = format_content(
                ContentType.ANIMATION, AnimationContentData(file_name)
            )
            append_to_note(markdown_link)
        else:
            file_id = animation.file_id

            markdown_link = format_content(ContentType.ANIMATION, BigMediaData(file_id))
            append_to_note(markdown_link)

        # Проверяем, есть ли подпись к фото
        caption = update.message.caption
        if caption:
            formatted_caption = format_content(
                ContentType.CAPTION, TextContentData(caption)
            )
            append_to_note(formatted_caption)
            await update.message.reply_text(
                "Анимация и подпись добавлены в заметку. #animation"
            )
        else:
            await update.message.reply_text("Анимация добавлено в заметку. #animation")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении Анимации: {str(e)}")
        logger.error(f"Error in handle_animation: {str(e)}")
