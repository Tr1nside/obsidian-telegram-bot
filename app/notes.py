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
    TEMP_FOLDER,
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


def _generate_filename(type: ContentType, update: Update = None) -> str:
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
            return f"[Big Video: {file_id}]"
        case ContentType.STICKER, StickerContentData(file_name):
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
        file_path = os.path.join(TEMP_FOLDER, file_name)

        response = requests.get(file.file_path)
        with open(file_path, "wb") as f:
            f.write(response.content)

        # Добавляем фото в заметку
        markdown_link = _format_content(ContentType.PHOTO, PhotoContentData(file_name))
        append_to_note(markdown_link)

        # Проверяем, есть ли подпись к фото
        caption = update.message.caption
        if caption:
            formatted_caption = _format_content(
                ContentType.CAPTION, TextContentData(caption)
            )
            append_to_note(formatted_caption)
            await update.message.reply_text(
                "Фото и подпись добавлены в заметку. #photo"
            )
        else:
            await update.message.reply_text("Фото добавлено в заметку. #photo")
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

        formatted_transcript = _format_content(
            ContentType.TRANSCRIPT, TranscriptContentData(transcript_text)
        )
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


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function for handle video messege. Add video and capture to current note"""
    if not is_allowed_user(update):
        return
    try:
        video = update.message.video

        if video.file_size < 20971520:
            file = await video.get_file()
            file_name = _generate_filename(ContentType.VIDEO)
            file_path = os.path.join(TEMP_FOLDER, file_name)

            response = requests.get(file.file_path, stream=True)
            with open(file_path, "wb") as f:
                f.write(response.content)

            # Добавляем фото в заметку
            markdown_link = _format_content(
                ContentType.VIDEO, VideoContentData(file_name)
            )
            append_to_note(markdown_link)
        else:
            file_id = video.file_id

            markdown_link = _format_content(ContentType.VIDEO, BigMediaData(file_id))
            append_to_note(markdown_link)

        # Проверяем, есть ли подпись к фото
        caption = update.message.caption
        if caption:
            formatted_caption = _format_content(
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


async def handle_animation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function for handle gif messege. Add gif and capture to current note"""
    if not is_allowed_user(update):
        return
    try:
        animation = update.message.animation

        if animation.file_size < 52428800:
            file = await animation.get_file()
            file_name = _generate_filename(ContentType.ANIMATION)
            file_path = os.path.join(TEMP_FOLDER, file_name)

            response = requests.get(file.file_path)
            with open(file_path, "wb") as f:
                f.write(response.content)

            # Добавляем фото в заметку
            markdown_link = _format_content(
                ContentType.ANIMATION, AnimationContentData(file_name)
            )
            append_to_note(markdown_link)
        else:
            file_id = animation.file_id

            markdown_link = _format_content(
                ContentType.ANIMATION, BigMediaData(file_id)
            )
            append_to_note(markdown_link)

        # Проверяем, есть ли подпись к фото
        caption = update.message.caption
        if caption:
            formatted_caption = _format_content(
                ContentType.CAPTION, TextContentData(caption)
            )
            append_to_note(formatted_caption)
            await update.message.reply_text(
                "Анимация и подпись добавлены в заметку. #animation"
            )
        else:
            await update.message.reply_text("Анимация добавлено в заметку. #animation")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении Анимации: {str(e)}")
        logger.error(f"Error in handle_animation: {str(e)}")


async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function to handle sticker message. Add sticker image to current note"""
    if not is_allowed_user(update):
        return
    try:
        sticker = update.message.sticker
        file = await sticker.get_file()
        file_name = _generate_filename(ContentType.STICKER, update)  # Передаем update
        file_path = os.path.join(TEMP_FOLDER, file_name)

        response = requests.get(file.file_path)
        with open(file_path, "wb") as f:
            f.write(response.content)

        # Добавляем стикер в заметку
        markdown_link = _format_content(
            ContentType.STICKER, StickerContentData(file_name)
        )
        append_to_note(markdown_link)

        # Проверяем, есть ли подпись к стикеру
        caption = update.message.caption
        if caption:
            formatted_caption = _format_content(
                ContentType.CAPTION, TextContentData(caption)
            )
            append_to_note(formatted_caption)
            await update.message.reply_text(
                "Стикер и подпись добавлены в заметку. #sticker"
            )
        else:
            await update.message.reply_text("Стикер добавлен в заметку. #sticker")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении стикера: {str(e)}")
        logger.error(f"Error in handle_sticker: {str(e)}")
