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
    VideoContentData,
    BigMediaData,
    ContentType,
)


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function for handle video messege. Add video and capture to current note"""
    if not is_allowed_user(update):
        return
    try:
        video = update.message.video

        if video.file_size < 20971520:
            file = await video.get_file()
            file_name = generate_filename(ContentType.VIDEO)
            file_path = os.path.join(TEMP_FOLDER, file_name)

            response = requests.get(file.file_path, stream=True)
            with open(file_path, "wb") as f:
                f.write(response.content)

            # Добавляем фото в заметку
            markdown_link = format_content(
                ContentType.VIDEO, VideoContentData(file_name)
            )
            append_to_note(markdown_link)
        else:
            file_id = video.file_id

            markdown_link = format_content(ContentType.VIDEO, BigMediaData(file_id))
            append_to_note(markdown_link)

        # Проверяем, есть ли подпись к фото
        caption = update.message.caption
        if caption:
            formatted_caption = format_content(
                ContentType.CAPTION, TextContentData(caption)
            )
            append_to_note(formatted_caption)
            await update.message.reply_text(
                "Видео и подпись добавлены в заметку. #video"
            )
        else:
            await update.message.reply_text("Видео добавлено в заметку. #video")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении Видео: {str(e)}")
        logger.error(f"Error in handle_video: {str(e)}")
