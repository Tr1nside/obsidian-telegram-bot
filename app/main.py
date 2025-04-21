import os
import requests
import whisper
import warnings
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from datetime import datetime
import uuid
from pydub import AudioSegment
import logging
from dotenv import load_dotenv
import asyncio

# Загружаем переменные из .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Подавление предупреждения FP16
warnings.filterwarnings("ignore", category=UserWarning)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="bot.log"
)
logger = logging.getLogger(__name__)

# Конфигурация
ALLOWED_USER_ID = 1316772009
OBSIDIAN_VAULT_PATH = r"C:\Users\Chertila\Documents\Personal Notes"
NOTES_FOLDER = os.path.join(OBSIDIAN_VAULT_PATH, r"0. Файлы\Inbox")
PHOTOS_FOLDER = os.path.join(OBSIDIAN_VAULT_PATH, r"0. Файлы\01 - кэш")
AUDIO_TEMP_FOLDER = os.path.join(OBSIDIAN_VAULT_PATH, r"0. Файлы\01 - кэш")

# Инициализация Whisper
WHISPER_MODEL = "medium"
model = whisper.load_model(WHISPER_MODEL)

# Глобальная переменная для текущего файла заметки
current_note_file = None

# Создание папок
os.makedirs(NOTES_FOLDER, exist_ok=True)
os.makedirs(PHOTOS_FOLDER, exist_ok=True)
os.makedirs(AUDIO_TEMP_FOLDER, exist_ok=True)

# Список команд для меню
commands = [
    BotCommand(command="start", description="Запустить бота"),
    BotCommand(command="newnote", description="Создать новую заметку"),
    BotCommand(command="printnote", description="Посмотреть текущую заметку"),
    BotCommand(command="listnotes", description="Показать список заметок"),
    BotCommand(command="deletenote", description="Удалить текущую заметку"),
    BotCommand(command="selectnote", description="Выбрать заметку по номеру"),
]

# Функция для проверки user_id
def is_allowed_user(update: Update) -> bool:
    if update.message is None or update.message.from_user is None:
        return False
    return update.message.from_user.id == ALLOWED_USER_ID

# Функция для создания нового файла заметки
def create_new_note():
    global current_note_file
    note_id = str(uuid.uuid4())[:4]
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    note_filename = f"Note_{timestamp}_{note_id}.md"
    current_note_file = os.path.join(NOTES_FOLDER, note_filename)
    with open(current_note_file, "w", encoding="utf-8") as f:
        f.write(f"# Note {timestamp}\n\n")
    return current_note_file

# Функция для добавления контента в текущую заметку
def append_to_note(content):
    if current_note_file is None:
        create_new_note()
    with open(current_note_file, "a", encoding="utf-8") as f:
        f.write(content + "\n")

# Функция обработки ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text("Произошла ошибка. Попробуй снова или напиши администратору.")

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.from_user.id
        await update.message.reply_text(
            f"Бот запущен! Ваш user_id: {user_id}\n"
            "Скопируйте этот ID и добавьте его в ALLOWED_USER_ID.\n"
            "Отправляйте текст, фото или голосовые сообщения. "
            "Используйте /newnote для создания новой заметки, /printnote для отправки текущей, "
            "/listnotes для списка заметок или /deletenote для удаления текущей."
        )
        if current_note_file is None:
            create_new_note()
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")
        logger.error(f"Error in start: {str(e)}")


# Обработчик команды /newnote
async def new_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_user(update):
        return
    try:
        global current_note_file
        current_note_file = create_new_note()
        await update.message.reply_text(f"Создана новая заметка: {os.path.basename(current_note_file)}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при создании заметки: {str(e)}")
        logger.error(f"Error in new_note: {str(e)}")

# Обработчик команды /printnote
async def print_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_user(update):
        return
    try:
        if current_note_file is None or not os.path.exists(current_note_file):
            await update.message.reply_text("Нет активной заметки. Создайте новую с помощью /newnote.")
            return
        with open(current_note_file, "r", encoding="utf-8") as f:
            note_content = f.read()
        if len(note_content) <= 4096:
            await update.message.reply_text(f"Содержимое заметки:\n\n{note_content}")
        else:
            with open(current_note_file, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=os.path.basename(current_note_file),
                    caption="Заметка слишком длинная, отправляю как файл."
                )
        await update.message.reply_text("Заметка отправлена.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при отправке заметки: {str(e)}")
        logger.error(f"Error in print_note: {str(e)}")

# Обработчик команды /listnotes
async def list_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_user(update):
        return
    try:
        notes = [f for f in os.listdir(NOTES_FOLDER) if f.endswith(".md")]
        if not notes:
            await update.message.reply_text("Папка с заметками пуста.")
            return
        response = "Список заметок:\n"
        for idx, note in enumerate(notes, start=1):
            file_path = os.path.join(NOTES_FOLDER, note)
            creation_time = datetime.fromtimestamp(os.path.getctime(file_path)).strftime("%d-%m-%Y %H:%M:%S")
            response += f"{idx}. {note} (Создано: {creation_time})\n"
        context.user_data['notes_list'] = notes
        if len(response) <= 4096:
            await update.message.reply_text(response)
        else:
            temp_file = os.path.join(AUDIO_TEMP_FOLDER, "notes_list.txt")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(response)
            with open(temp_file, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename="notes_list.txt",
                    caption="Список заметок слишком длинный, отправляю как файл."
                )
            os.remove(temp_file)
    except Exception as e:
        await update.message.reply_text(f"Ошибка при получении списка заметок: {str(e)}")
        logger.error(f"Error in list_notes: {str(e)}")

# Обработчик команды /selectnote
async def select_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_user(update):
        return
    try:
        if 'notes_list' not in context.user_data:
            await update.message.reply_text("Сначала получите список заметок с помощью /listnotes.")
            return
        args = context.args
        if not args:
            await update.message.reply_text("Укажите индекс заметки. Пример: /selectnote 1")
            return
        try:
            index = int(args[0]) - 1
            notes = context.user_data['notes_list']
            if index < 0 or index >= len(notes):
                await update.message.reply_text("Неверный индекс заметки.")
                return
            selected_note = notes[index]
            global current_note_file
            current_note_file = os.path.join(NOTES_FOLDER, selected_note)
            with open(current_note_file, "r", encoding="utf-8") as f:
                note_content = f.read()
            if len(note_content) <= 4096:
                await update.message.reply_text(f"Выбрана заметка: {selected_note}\n\nСодержимое:\n{note_content}")
            else:
                with open(current_note_file, "rb") as f:
                    await update.message.reply_document(
                        document=f,
                        filename=selected_note,
                        caption=f"Выбрана заметка: {selected_note}. Содержимое слишком длинное, отправляю как файл."
                    )
        except ValueError:
            await update.message.reply_text("Индекс должен быть числом.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при выборе заметки: {str(e)}")
        logger.error(f"Error in select_note: {str(e)}")

# Обработчик команды /deletenote
async def delete_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_user(update):
        return
    try:
        global current_note_file
        if current_note_file is None or not os.path.exists(current_note_file):
            await update.message.reply_text("Нет активной заметки для удаления.")
            return
        os.remove(current_note_file)
        note_name = os.path.basename(current_note_file)
        current_note_file = None
        await update.message.reply_text(f"Заметка {note_name} удалена.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при удалении заметки: {str(e)}")
        logger.error(f"Error in delete_note: {str(e)}")

# Обработчик текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_user(update):
        return
    try:
        text = update.message.text
        formatted_text = f"{text}\n"
        append_to_note(formatted_text)
        await update.message.reply_text("Текст добавлен в заметку.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении текста: {str(e)}")
        logger.error(f"Error in handle_text: {str(e)}")

# Обработчик фотографий
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_user(update):
        return
    try:
        photo = update.message.photo[-1]  # Берем фото наилучшего качества
        file = await photo.get_file()
        file_name = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}.jpg"
        file_path = os.path.join(PHOTOS_FOLDER, file_name)
        
        response = requests.get(file.file_path)
        with open(file_path, "wb") as f:
            f.write(response.content)
        
        # Добавляем фото в заметку
        markdown_link = f"![[{file_name}|300]]\n"
        append_to_note(markdown_link)
        
        # Проверяем, есть ли подпись к фото
        caption = update.message.caption
        if caption:
            formatted_caption = f"{caption}\n"
            append_to_note(formatted_caption)
        
        await update.message.reply_text("Фото и подпись (если была) добавлены в заметку.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении фото: {str(e)}")
        logger.error(f"Error in handle_photo: {str(e)}")


# Обработчик голосовых сообщений
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_user(update):
        return
    try:
        voice = update.message.voice
        file = await voice.get_file()
        file_name = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())}.ogg"
        ogg_path = os.path.join(AUDIO_TEMP_FOLDER, file_name)
        response = requests.get(file.file_path)
        with open(ogg_path, "wb") as f:
            f.write(response.content)
        wav_path = ogg_path.replace(".ogg", ".wav")
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format="wav")
        result = model.transcribe(wav_path, language="ru")
        transcript_text = result["text"]
        formatted_transcript = f"[Voice Transcript]: \n{transcript_text}\n"
        append_to_note(formatted_transcript)
        await update.message.reply_text("Голосовое сообщение транскрибировано и добавлено в заметку.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при транскрипции: {str(e)}")
        logger.error(f"Error in handle_voice: {str(e)}")
    finally:
        if os.path.exists(ogg_path):
            os.remove(ogg_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)

# Основная функция
def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("newnote", new_note))
    application.add_handler(CommandHandler("printnote", print_note))
    application.add_handler(CommandHandler("listnotes", list_notes))
    application.add_handler(CommandHandler("deletenote", delete_note))
    application.add_handler(CommandHandler("selectnote", select_note))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_error_handler(error_handler)

    # Устанавливаем меню команд асинхронно
    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.bot.set_my_commands(commands))
    logger.info("Меню команд успешно установлено")

    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()