from telegram import Update
from telegram.ext import ContextTypes
import requests
import os
import imageio
from .utils import is_allowed_user, append_to_note, format_content, generate_filename, ContentType, AnimationContentData, BigMediaData, TextContentData
from config import logger, TEMP_FOLDER

def _convert_to_gif(mp4_file_name: str, mp4_file_path: str) -> str:
    gif_file_name = mp4_file_name.replace('.mp4', '.gif')
    gif_file_path = os.path.join(TEMP_FOLDER, gif_file_name)
    reader = imageio.get_reader(mp4_file_path)
    writer = imageio.get_writer(gif_file_path, format='GIF', fps=reader.get_meta_data()['fps'])
    for frame in reader:
        writer.append_data(frame)
    writer.close()
    reader.close()
    return gif_file_name, gif_file_path

async def handle_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function for handle gif message. Download as MP4, convert to GIF, and add to current note"""
    if not is_allowed_user(update):
        return
    try:
        animation = update.message.animation

        if animation.file_size < 52428800:
            file = await animation.get_file()
            mp4_file_name = f"temp_{generate_filename(ContentType.ANIMATION)}"
            mp4_file_path = os.path.join(TEMP_FOLDER, mp4_file_name)

            response = requests.get(file.file_path)
            with open(mp4_file_path, "wb") as f:
                f.write(response.content)

            gif_file_name, gif_file_path = _convert_to_gif(mp4_file_name, mp4_file_path)

            markdown_link = format_content(
                ContentType.ANIMATION, AnimationContentData(gif_file_name)
            )
            append_to_note(markdown_link)

            # Удаляем временный MP4
            os.remove(mp4_file_path)
        else:
            file_id = animation.file_id

            markdown_link = format_content(
                ContentType.ANIMATION, BigMediaData(file_id)
            )
            append_to_note(markdown_link)

        # Проверяем, есть ли подпись к анимации
        caption = update.message.caption
        if caption:
            formatted_caption = format_content(
                ContentType.CAPTION, TextContentData(caption)
            )
            append_to_note(formatted_caption)
            await update.message.reply_text(
                "GIF и подпись добавлены в заметку. #animation"
            )
        else:
            await update.message.reply_text("GIF добавлен в заметку. #animation")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении GIF: {str(e)}")
        logger.error(f"Error in handle_animation: {str(e)}")
    finally:
        # Удаляем временные файлы, если они остались
        if 'mp4_file_path' in locals() and os.path.exists(mp4_file_path):
            os.remove(mp4_file_path)
        if 'gif_file_path' in locals() and os.path.exists(gif_file_path) and animation.file_size >= 52428800:
            os.remove(gif_file_path)