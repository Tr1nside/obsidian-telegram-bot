from telegram import Update
from telegram.ext import ContextTypes
import requests
import os
from config import TEMP_FOLDER, logger
from .utils import is_allowed_user, append_to_note, generate_filename, format_content, TextContentData, ContentType, StickerContentData, mp4_to_gif, tgs_to_gif, set_reaction

async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Функция для обработки сообщений со стикерами. Добавляет стикер в текущую заметку."""
    if not is_allowed_user(update):
        return
    
    await set_reaction(update, context)
    
    try:
        # Проверяем существование TEMP_FOLDER и создаем, если не существует
        os.makedirs(TEMP_FOLDER, exist_ok=True)

        sticker = update.message.sticker
        file = await sticker.get_file()
        file_name = generate_filename(ContentType.STICKER, update)
        file_path = os.path.join(TEMP_FOLDER, file_name)

        # Загружаем файл стикера с использованием контекстного менеджера
        with requests.get(file.file_path, stream=True) as response:
            response.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        # Обрабатываем анимированные или видео стикеры
        if sticker.is_video:
            gif_file_name = mp4_to_gif(file_path, file_name)
            file_name = os.path.basename(gif_file_name)  # Обновляем имя файла

        if sticker.is_animated:
            gif_file_name = await tgs_to_gif(file_path, file_name)
            file_name = os.path.basename(gif_file_name)  # Обновляем имя файла
            

        # Добавляем стикер в заметку
        markdown_link = format_content(ContentType.STICKER, StickerContentData(file_name))
        append_to_note(markdown_link)
        await update.message.reply_text("Стикер добавлен в заметку. #sticker")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении стикера: {str(e)}")
        logger.error(f"Ошибка в handle_sticker: {str(e)}")
