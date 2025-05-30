from telegram import Update
from telegram.ext import ContextTypes
import requests
import os
from .utils import (
    is_allowed_user,
    append_to_note,
    format_content,
    generate_filename,
    mp4_to_gif,
    ContentType,
    AnimationContentData,
    BigMediaData,
    main_decorator,
)
from config import logger, TEMP_FOLDER
from .caption import append_caption


@main_decorator
async def handle_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция для обработки GIF-сообщений. Скачивает как MP4, конвертирует в GIF и добавляет в заметку."""
    if not is_allowed_user(update):
        return

    mp4_file_path = None
    try:
        # Проверяем существование TEMP_FOLDER и создаем, если не существует
        os.makedirs(TEMP_FOLDER, exist_ok=True)

        animation = update.message.animation
        if animation.file_size < 52428800:  # 50 MB
            file = await animation.get_file()
            gif_file_name = generate_filename(ContentType.ANIMATION, update)
            mp4_file_name = f"temp_{gif_file_name.replace('.gif', '.mp4')}"
            mp4_file_path = os.path.join(TEMP_FOLDER, mp4_file_name)

            # Скачиваем MP4
            with requests.get(file.file_path, stream=True) as response:
                response.raise_for_status()
                with open(mp4_file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

            # Конвертируем в GIF
            mp4_to_gif(mp4_file_path, gif_file_name)

            # Форматируем и добавляем в заметку
            markdown_link = format_content(
                ContentType.ANIMATION, AnimationContentData(gif_file_name)
            )
            append_caption(update)
            append_to_note(markdown_link)
            await update.message.reply_text(
                "GIF и подпись добавлены в заметку. #animation"
            )
        else:
            file_id = animation.file_id
            markdown_link = format_content(ContentType.ANIMATION, BigMediaData(file_id))
            append_caption(update)
            append_to_note(markdown_link)
            await update.message.reply_text(
                "GIF и подпись добавлены в заметку. #animation"
            )

    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении GIF: {str(e)}")
        logger.error(f"Ошибка в handle_animation: {str(e)}")
    finally:
        # Удаляем временный файл, если он существует
        if mp4_file_path and os.path.exists(mp4_file_path):
            os.remove(mp4_file_path)
