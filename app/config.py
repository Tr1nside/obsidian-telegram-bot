from dotenv import load_dotenv
import os
import whisper
import logging

# Загружаем токен из .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Конфигурация
ALLOWED_USER_ID = 1316772009
OBSIDIAN_VAULT_PATH = r"C:\Users\Chertila\Documents\Personal Notes"
NOTES_FOLDER = os.path.join(OBSIDIAN_VAULT_PATH, r"0. Файлы\Inbox")
PHOTOS_FOLDER = os.path.join(OBSIDIAN_VAULT_PATH, r"0. Файлы\01 - кэш")
AUDIO_TEMP_FOLDER = os.path.join(OBSIDIAN_VAULT_PATH, r"0. Файлы\01 - кэш")

# Создание папок
os.makedirs(NOTES_FOLDER, exist_ok=True)
os.makedirs(PHOTOS_FOLDER, exist_ok=True)
os.makedirs(AUDIO_TEMP_FOLDER, exist_ok=True)

# Глобальная переменная для текущего файла заметки
current_note_file = None

# Инициализация Whisper
WHISPER_MODEL = "medium"
model = whisper.load_model(WHISPER_MODEL)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="bot.log",
)
logger = logging.getLogger(__name__)