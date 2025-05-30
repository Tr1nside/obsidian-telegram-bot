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
    VideoContentData,
    ContentType,
    main_decorator
)

@main_decorator
async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function to handle video note message. Add video note to current note"""
    if not is_allowed_user(update):
        return

    
    try:
        video_note = update.message.video_note

        file = await video_note.get_file()
        if file is None or file.file_path is None:
            await update.message.reply_text("Ошибка: не удалось получить файл видеосообщения.")
            logger.error("Error in handle_video_note: file or file_path is None")
            return

        file_name = generate_filename(ContentType.VIDEO)
        file_path = os.path.join(TEMP_FOLDER, file_name)

        response = requests.get(file.file_path, stream=True)
        if response.status_code != 200:
            await update.message.reply_text("Ошибка: не удалось скачать видеосообщение.")
            logger.error(f"Error in handle_video_note: HTTP {response.status_code}")
            return

        with open(file_path, "wb") as f:
            f.write(response.content)

        # Добавляем видеосообщение в заметку
        markdown_link = format_content(
            ContentType.VIDEO, VideoContentData(file_name)
        )
        append_to_note(markdown_link)
        await update.message.reply_text(
            "Видеосообщение добавлено в заметку. #video_note"
        )
        
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении видеосообщения: {str(e)}")
        logger.error(f"Error in handle_video_note: {str(e)}")
