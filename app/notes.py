from telegram import Update
from telegram.ext import (
    ContextTypes,
)
from datetime import datetime
from enum import Enum, auto
from pydub import AudioSegment
from dataclasses import dataclass
import requests
import uuid
import os


from config import (
    ALLOWED_USER_ID,
    NOTES_FOLDER,
    PHOTOS_FOLDER,
    AUDIO_TEMP_FOLDER,
    logger,
    model,
    note_manager,
)


class ContentType(Enum):
    TEXT = auto()
    CAPTION = auto()
    TRANSCRIPT = auto()
    PHOTO = auto()

@dataclass
class TextContentData:
    text: str


@dataclass
class PhotoContentData:
    file_name: str


@dataclass
class TranscriptContentData:
    transcript_text: str


ContentData = (TextContentData | PhotoContentData | TranscriptContentData)

def is_allowed_user(update: Update) -> bool:
    """Function for user verification"""
    if update.message is None or update.message.from_user is None:
        return False
    return update.message.from_user.id == ALLOWED_USER_ID


def _generate_id() -> str:
    """Function for generation id for files"""
    return str(uuid.uuid4())[:4]


def _generate_filename(type: ContentType) -> str:
    """Function for generation filename"""
    match type:
        case ContentType.TEXT:
            note_id = _generate_id()
            timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            filename = f"TG_Note_{timestamp}_{note_id}.md"
            return filename
        case ContentType.PHOTO:
            filename = (
                f"TG_photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_generate_id()}.jpg"
            )
            return filename
        case ContentType.TRANSCRIPT:
            filename = (
                f"TG_voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_generate_id()}.ogg"
            )
            return filename


def create_new_note():
    """Function for create new note"""
    note_filename = _generate_filename(ContentType.TEXT)
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


def _format_content(type: ContentType, data: ContentData) -> str:
    """Function for formating content to be added to the note"""
    match type, data:
        case (ContentType.TEXT, TextContentData(text)) | (ContentType.CAPTION, TextContentData(text)):
            return f"{text}\n"
        case ContentType.TRANSCRIPT, TranscriptContentData(transcript_text):
            return f"[Voice Transcript]: \n{transcript_text}\n"
        case ContentType.PHOTO, PhotoContentData(file_name):
            return f"![[{file_name}|300]]\n"


# Handles
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function for handle text messege. Add text to current note"""
    if not is_allowed_user(update):
        return
    try:
        text = update.message.text
        formatted_text = _format_content(ContentType.TEXT, TextContentData(text))
        append_to_note(formatted_text)
        await update.message.reply_text("Текст добавлен в заметку.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении текста: {str(e)}")
        logger.error(f"Error in handle_text: {str(e)}")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function for handle photo messege. Add photo and capture to current note"""
    if not is_allowed_user(update):
        return
    try:
        photo = update.message.photo[-1]  # Берем фото наилучшего качества
        file = await photo.get_file()
        file_name = _generate_filename(ContentType.PHOTO)
        file_path = os.path.join(PHOTOS_FOLDER, file_name)

        response = requests.get(file.file_path)
        with open(file_path, "wb") as f:
            f.write(response.content)

        # Добавляем фото в заметку
        markdown_link = _format_content(ContentType.PHOTO, PhotoContentData(file_name))
        append_to_note(markdown_link)

        # Проверяем, есть ли подпись к фото
        caption = update.message.caption
        if caption:
            formatted_caption = _format_content(ContentType.CAPTION, TextContentData(caption))
            append_to_note(formatted_caption)
            await update.message.reply_text("Фото и подпись добавлены в заметку.")
        else:
            await update.message.reply_text("Фото и подпись добавлены в заметку.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении фото: {str(e)}")
        logger.error(f"Error in handle_photo: {str(e)}")


def _convert_ogg_to_wav(ogg_path: str) -> str:
    """Converts OGG to WAV and returns the path to the WAV file"""
    if not ogg_path or not os.path.exists(ogg_path):
        raise FileNotFoundError("OGG file not found")

    wav_path = ogg_path.replace(".ogg", ".wav")
    audio = AudioSegment.from_ogg(ogg_path)
    audio.export(wav_path, format="wav")

    return wav_path


async def _download_voice_file(voice) -> str:
    """Downloads a voice message and returns the path to the OGG file"""
    file = await voice.get_file()
    file_name = _generate_filename(ContentType.TRANSCRIPT)
    ogg_path = os.path.join(AUDIO_TEMP_FOLDER, file_name)

    response = requests.get(file.file_path)
    with open(ogg_path, "wb") as f:
        f.write(response.content)

    return ogg_path


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed_user(update):
        return
    try:
        voice = update.message.voice
        ogg_path = await _download_voice_file(voice)
        wav_path = _convert_ogg_to_wav(ogg_path)

        result = model.transcribe(wav_path, language="ru")
        transcript_text = result["text"]

        formatted_transcript = _format_content(ContentType.TRANSCRIPT, TranscriptContentData(transcript_text))
        append_to_note(formatted_transcript)

        await update.message.reply_text(
            "Голосовое сообщение транскрибировано и добавлено в заметку."
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка при транскрипции: {str(e)}")
        logger.error(f"Error in handle_voice: {str(e)}")
    finally:
        if ogg_path and os.path.exists(ogg_path):
            os.remove(ogg_path)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)


def transcribe_audio(wav_path: str) -> str:
    """Transcribes an audio file and returns the text"""
    if not wav_path or not os.path.exists(wav_path):
        raise FileNotFoundError("WAV file not found")

    result = model.transcribe(wav_path, language="ru")
    return result["text"]


def cleanup_temp_files(*file_paths):
    """Cleans up temporary files"""
    for path in file_paths:
        if path and os.path.exists(path):
            os.remove(path)
