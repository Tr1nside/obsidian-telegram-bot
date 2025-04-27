from telegram import Update
from datetime import datetime
from enum import Enum, auto
from dataclasses import dataclass
from moviepy.editor import VideoFileClip
import uuid
import os
from PIL import Image
import numpy as np
from typing import Union
import pylottie  
import asyncio
from concurrent.futures import ThreadPoolExecutor


from config import ALLOWED_USER_ID, NOTES_FOLDER, note_manager, TEMP_FOLDER, logger

class ContentType(Enum):
    TEXT = auto()
    CAPTION = auto()
    TRANSCRIPT = auto()
    PHOTO = auto()
    VIDEO = auto()
    ANIMATION = auto()
    STICKER = auto()


@dataclass
class TextContentData:
    text: str


@dataclass
class PhotoContentData:
    file_name: str


@dataclass
class StickerContentData:
    file_name: str


@dataclass
class VideoContentData:
    file_name: str


@dataclass
class AnimationContentData:
    file_name: str


@dataclass
class BigMediaData:
    file_id: int


@dataclass
class TranscriptContentData:
    transcript_text: str


ContentData = Union[
    TextContentData,
    PhotoContentData,
    TranscriptContentData,
    VideoContentData,
    AnimationContentData,
    BigMediaData,
    StickerContentData,
]


def is_allowed_user(update: Update) -> bool:
    """Проверка, является ли пользователь разрешенным."""
    if update.message is None or update.message.from_user is None:
        return False
    return update.message.from_user.id == ALLOWED_USER_ID


def _generate_id() -> str:
    """Генерация уникального идентификатора для файлов."""
    return str(uuid.uuid4())[:4]


def generate_filename(type: ContentType, update: Update = None) -> str:
    """Генерация имени файла на основе типа контента."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    match type:
        case ContentType.TEXT:
            note_id = _generate_id()
            return f"TG_Note_{timestamp}_{note_id}.md"
        case ContentType.PHOTO:
            return f"TG_photo_{timestamp}_{_generate_id()}.jpg"
        case ContentType.VIDEO:
            return f"TG_video_{timestamp}_{_generate_id()}.mp4"
        case ContentType.TRANSCRIPT:
            return f"TG_voice_{timestamp}_{_generate_id()}.ogg"
        case ContentType.ANIMATION:
            return f"TG_animation_{timestamp}_{_generate_id()}.gif"
        case ContentType.STICKER:
            filename = f"TG_sticker_{timestamp}_{_generate_id()}"
            if update and hasattr(update.message, "sticker") and update.message.sticker:
                if update.message.sticker.is_animated or update.message.sticker.is_video:
                    return filename + ".gif"
                return filename + ".webp"
            return filename + ".webp"


def create_new_note():
    """Создание новой заметки."""
    os.makedirs(NOTES_FOLDER, exist_ok=True)
    note_filename = generate_filename(ContentType.TEXT)
    note_path = os.path.join(NOTES_FOLDER, note_filename)
    note_manager.set_current_note_file(note_path)

    with open(note_path, "w", encoding="utf-8") as f:
        f.write("\n")
    return note_path


def append_to_note(content: str):
    """Добавление контента в текущую заметку."""
    if note_manager.get_current_note_file() is None:
        create_new_note()
    with open(note_manager.get_current_note_file(), "a", encoding="utf-8") as f:
        f.write(content + "\n")


def format_content(type: ContentType, data: ContentData) -> str:
    """Форматирование контента для добавления в заметку."""
    match type, data:
        case (ContentType.TEXT | ContentType.CAPTION, TextContentData(text)):
            return f"{text}\n"
        case ContentType.TRANSCRIPT, TranscriptContentData(transcript_text):
            return f"[Voice Transcript]: \n{transcript_text}\n"
        case ContentType.PHOTO, PhotoContentData(file_name):
            return f"![[{file_name}|300]]\n"
        case ContentType.VIDEO, VideoContentData(file_name):
            return f"![[{file_name}]]\n"
        case (ContentType.VIDEO | ContentType.ANIMATION, BigMediaData(file_id)):
            return f"[Big Media: {file_id}]"
        case (ContentType.STICKER | ContentType.ANIMATION, AnimationContentData(file_name) | StickerContentData(file_name)):
            return f"![[{file_name}|300]]\n"


def mp4_to_gif(input_path: str, filename: str, fps: int = 80, scale: float = 0.5) -> str:
    """Конвертация MP4 в GIF."""
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    output_path = os.path.join(TEMP_FOLDER, filename)

    try:
        with VideoFileClip(input_path) as clip:
            # Получаем новые размеры
            new_width = int(clip.w * scale)
            new_height = int(clip.h * scale)

            # Функция для изменения размера кадра
            def resize_frame(frame):
                pil_image = Image.fromarray(frame)
                resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                return np.array(resized_image)

            # Применяем изменение размера к видео
            resized_clip = clip.fl_image(resize_frame)
            resized_clip.write_gif(output_path, fps=fps)
    except Exception as e:
        logger.error(f"Ошибка конвертации MP4 в GIF: {str(e)}")
        raise
    return output_path


def tgs_to_gif(input_path: str, output_filename: str, fps: int = 30, scale: float = 0.5) -> str:
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    output_path = os.path.join(TEMP_FOLDER, output_filename)
    if not output_filename.endswith(".gif"):
        output_filename += ".gif"
        output_path = os.path.join(TEMP_FOLDER, output_filename)
    def sync_convert():
        pylottie.convertLottie2GIF(input_path, output_path)
        if not os.path.exists(output_path):
            raise ValueError(f"Не удалось создать GIF из {input_path}")
        return output_path
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return loop.run_in_executor(pool, sync_convert)