from dotenv import load_dotenv
import os
import whisper
import logging

# Загружаем токен из .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Конфигурация
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID"))
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH").replace("\\", "/")
NOTES_FOLDER = os.getenv("NOTES_FOLDER").replace("\\", "/")
TEMP_FOLDER = os.getenv("TEMP_FOLDER").replace("\\", "/")
AUDIO_TEMP_FOLDER = os.getenv("AUDIO_TEMP_FOLDER").replace("\\", "/")
ATTACH_FOLDER = os.getenv("ATTACH_FOLDER").replace("\\", "/")


# Создание папок
os.makedirs(NOTES_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)
os.makedirs(AUDIO_TEMP_FOLDER, exist_ok=True)
os.makedirs(ATTACH_FOLDER, exist_ok=True)


# Глобальная переменная для текущего файла заметки
class NoteManager:
    def __init__(self):
        self.current_note_file = None

    def set_current_note_file(self, file_path: str):
        self.current_note_file = file_path

    def get_current_note_file(self) -> str:
        return self.current_note_file


# Создаем экземпляр NoteManager
note_manager = NoteManager()

# Инициализация Whisper
WHISPER_MODEL = "tiny"
model = whisper.load_model(WHISPER_MODEL)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="bot.log",
)
logger = logging.getLogger(__name__)
