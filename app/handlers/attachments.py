from telegram import Update
from telegram.ext import (
    ContextTypes,
)
import requests
import os
from config import (
    ATTACH_FOLDER,
    logger,
)
from .utils import (
    is_allowed_user,
    append_to_note,
    format_content,
    DocumentContentData,
    BigMediaData,
    ContentType,
    set_reaction
)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function to handle document messages. Add document to current note and save to ATTACH_FOLDER with original filename"""
    if not is_allowed_user(update):
        return
    
    await set_reaction(update, context)
    
    try:
        document = update.message.document

        # Проверяем размер файла (20 МБ = 20 * 1024 * 1024 байт)
        if document.file_size < 20971520:
            file = await document.get_file()
            # Используем оригинальное имя файла или резервное, если file_name отсутствует
            file_name = document.file_name if document.file_name else f"document_{document.file_id}.bin"
            file_path = os.path.join(ATTACH_FOLDER, file_name)

            response = requests.get(file.file_path, stream=True)
            with open(file_path, "wb") as f:
                f.write(response.content)

            # Добавляем документ в заметку
            markdown_link = format_content(
                ContentType.DOCUMENT, DocumentContentData(file_name)
            )
            append_to_note(markdown_link)
            await update.message.reply_text(
                f"Документ добавлен в заметку: {file_name}. #document"
            )
        else:
            file_id = document.file_id

            markdown_link = format_content(ContentType.DOCUMENT, BigMediaData(file_id))
            append_to_note(markdown_link)
            await update.message.reply_text(
                f"Документ добавлен в заметку: {document.file_name or 'документ'}. #document"
            )
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении документа: {str(e)}")
        logger.error(f"Error in handle_document: {str(e)}")
