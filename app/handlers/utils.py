from telegram import Update
from datetime import datetime
from enum import Enum, auto
from dataclasses import dataclass
import uuid
import os
from config import ALLOWED_USER_ID, NOTES_FOLDER, note_manager

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

ContentData = (
    TextContentData
    | PhotoContentData
    | TranscriptContentData
    | VideoContentData
    | AnimationContentData
    | BigMediaData
    | StickerContentData
)

def is_allowed_user(update: Update) -> bool:
    """Function for user verification"""
    if update.message is None or update.message.from_user is None:
        return False
    return update.message.from_user.id == ALLOWED_USER_ID

def _generate_id() -> str:
    """Function for generation id for files"""
    return str(uuid.uuid4())[:4]

def generate_filename(type: ContentType, update: Update = None) -> str:
    """Function for generation filename"""
    match type:
        case ContentType.TEXT:
            note_id = _generate_id()
            timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            filename = f"TG_Note_{timestamp}_{note_id}.md"
            return filename
        case ContentType.PHOTO:
            filename = f"TG_photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_generate_id()}.jpg"
            return filename
        case ContentType.VIDEO:
            filename = f"TG_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_generate_id()}.mp4"
            return filename
        case ContentType.TRANSCRIPT:
            filename = f"TG_voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_generate_id()}.ogg1"
            return filename
        case ContentType.ANIMATION:
            filename = f"TG_animation_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_generate_id()}.mp4"
            return filename
        case ContentType.STICKER:
            filename = f"TG_sticker_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_generate_id()}"
            # Проверяем, анимированный или видео-стикер
            if update and hasattr(update.message, "sticker") and update.message.sticker:
                if (
                    update.message.sticker.is_animated
                    or update.message.sticker.is_video
                ):
                    return filename + ".mp4"  # Для анимированных и видео
                return filename + ".webp"  # Для статических
            return filename + ".webp"  # По умолчанию

def create_new_note():
    """Function for create new note"""
    note_filename = generate_filename(ContentType.TEXT)
    note_manager.set_current_note_file(os.path.join(NOTES_FOLDER, note_filename))

    with open(note_manager.get_current_note_file(), "w", encoding="utf-8") as f:
        f.write("\n")
    return note_manager.get_current_note_file()

def append_to_note(content: str):
    """Function for add content to current note"""
    if note_manager.get_current_note_file() is None:
        create_new_note()
    with open(note_manager.get_current_note_file(), "a", encoding="utf-8") as f:
        f.write(content + "\n")

def format_content(type: ContentType, data: ContentData) -> str:
    """Function for formatting content to be added to the note"""
    match type, data:
        case (
            (ContentType.TEXT, TextContentData(text))
            | (ContentType.CAPTION, TextContentData(text))
        ):
            return f"{text}\n"
        case ContentType.TRANSCRIPT, TranscriptContentData(transcript_text):
            return f"[Voice Transcript]: \n{transcript_text}\n"
        case ContentType.PHOTO, PhotoContentData(file_name):
            return f"![[{file_name}|300]]\n"
        case (
            (ContentType.VIDEO, VideoContentData(file_name))
            | (ContentType.ANIMATION, AnimationContentData(file_name))
        ):
            return f"![[{file_name}]]\n"
        case (
            (ContentType.VIDEO, BigMediaData(file_id))
            | (ContentType.ANIMATION, BigMediaData(file_id))
        ):
            return f"[Big Animation: {file_id}]"
        case ContentType.STICKER, StickerContentData(file_name):
            return f"![[{file_name}|300]]\n"