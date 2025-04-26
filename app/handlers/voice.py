from telegram import Update
from telegram.ext import (
    ContextTypes,
)
from pydub import AudioSegment
import requests
import os
from config import (
    AUDIO_TEMP_FOLDER,
    logger,
    model,
)

from .utils import (
    generate_filename,
    ContentType,
    TranscriptContentData,
    is_allowed_user,
    format_content,
    append_to_note,
)


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
    file_name = generate_filename(ContentType.TRANSCRIPT)
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

        formatted_transcript = format_content(
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
