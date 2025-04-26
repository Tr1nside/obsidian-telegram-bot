import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from enum import Enum, auto
from dataclasses import dataclass
from typing import List

from handlers.utils import create_new_note, is_allowed_user
from config import logger, NOTES_FOLDER, AUDIO_TEMP_FOLDER, note_manager


class MessageType(Enum):
    LISTNOTES = auto()
    START = auto()
    PRINTNOTE = auto()
    CALLBACK = auto()


@dataclass
class ListNotesData:
    notes: List[str]


@dataclass
class CallbackDataText:
    selected_note: str
    note_content: str


@dataclass
class CallbackDataFile:
    selected_note: str


@dataclass
class StartData:
    user_id: int


@dataclass
class PrintNoteData:
    note_content: str


MessageData = (
    StartData | ListNotesData | PrintNoteData | CallbackDataText | CallbackDataFile
)


def _format_message(type: MessageType, data: MessageData):
    match type, data:
        case MessageType.LISTNOTES, ListNotesData(notes):
            response = "Список заметок:\n"
            keyboard = []
            for idx, note in enumerate(notes):
                # file_path = os.path.join(NOTES_FOLDER, note)
                response += f"{note}\n"
                button = InlineKeyboardButton(
                    text=f"{note[:29]}",  # Текст на кнопке
                    callback_data=f"select_note_{idx}",  # Данные, которые вернутся
                )
                keyboard.append([button])  # Каждая кнопка в отдельном ряду
            return response, keyboard
        case MessageType.START, StartData(user_id):
            return f"Бот запущен! Ваш user_id: {user_id}\nСкопируйте этот ID и добавьте его в ALLOWED_USER_ID.\nОтправляйте текст, фото или голосовые сообщения. Используйте /newnote для создания новой заметки, /printnote для отправки текущей,/listnotes для списка заметок или /deletenote для удаления текущей."
        case MessageType.PRINTNOTE, PrintNoteData(note_content):
            return f"Содержимое заметки:\n\n{note_content}"
        case MessageType.CALLBACK, CallbackDataText(selected_note, note_content):
            return f"Выбрана заметка: {selected_note}\n\nСодержимое:\n{note_content}"
        case MessageType.CALLBACK, CallbackDataFile(selected_note):
            return f"**Выбрана заметка:** {selected_note} \nСодержимое слишком длинное, отправляю как файл."


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function for error handling"""
    logger.error(f"Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "Произошла ошибка. Попробуй снова или напиши администратору."
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        user_id = update.message.from_user.id
        await update.message.reply_text(
            _format_message(MessageType.START, StartData(user_id))
        )
        if note_manager.get_current_note_file() is None:
            create_new_note()
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")
        logger.error(f"Error in start: {str(e)}")


async def new_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /newnote command"""
    if not is_allowed_user(update):
        return
    try:
        note_manager.set_current_note_file(create_new_note())
        await update.message.reply_text(
            f"Создана новая заметка: {os.path.basename(note_manager.get_current_note_file())}"
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка при создании заметки: {str(e)}")
        logger.error(f"Error in new_note: {str(e)}")


def _check_current_note() -> bool:
    """Checks for current_note_file"""
    return note_manager.get_current_note_file() is None or not os.path.exists(
        note_manager.get_current_note_file()
    )


async def print_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /printnote command"""
    if not is_allowed_user(update):
        return
    try:
        if _check_current_note():
            await update.message.reply_text(
                "Нет активной заметки. Создайте новую с помощью /newnote."
            )
            return
        with open(note_manager.get_current_note_file(), "r", encoding="utf-8") as f:
            note_content = f.read()
        if len(note_content) <= 4096:
            await update.message.reply_text(
                _format_message(MessageType.PRINTNOTE, PrintNoteData(note_content))
            )
        else:
            with open(note_manager.get_current_note_file(), "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=os.path.basename(note_manager.get_current_note_file()),
                    caption="Заметка слишком длинная, отправляю как файл.",
                )
        await update.message.reply_text("Заметка отправлена.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка при отправке заметки: {str(e)}")
        logger.error(f"Error in print_note: {str(e)}")


async def list_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /listnotes command"""
    if not is_allowed_user(update):
        return
    try:
        notes = [f for f in os.listdir(NOTES_FOLDER) if f.endswith(".md")]
        if not notes:
            await update.message.reply_text("Папка с заметками пуста.")
            return

        response, keyboard = _format_message(
            MessageType.LISTNOTES, ListNotesData(notes)
        )

        reply_markup = InlineKeyboardMarkup(keyboard)

        context.user_data["notes_list"] = notes
        if len(response) <= 4096:
            await update.message.reply_text(response, reply_markup=reply_markup)
        else:
            temp_file = os.path.join(AUDIO_TEMP_FOLDER, "notes_list.txt")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(response)
            with open(temp_file, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename="notes_list.txt",
                    caption="Список заметок слишком длинный, отправляю как файл.",
                )
            os.remove(temp_file)
    except Exception as e:
        await update.message.reply_text(
            f"Ошибка при получении списка заметок: {str(e)}"
        )
        logger.error(f"Error in list_notes: {str(e)}")


def _check_index(index: int, notes: List[int]) -> bool:
    return index < 0 or index >= len(notes)


async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Подтверждаем получение callback-а

    try:
        if query.data.startswith("select_note_"):
            index = int(query.data.replace("select_note_", ""))
            notes = context.user_data.get("notes_list", [])

            if _check_index(index, notes):
                await query.message.reply_text("Неверный индекс заметки.")
                return

            selected_note = notes[index]
            note_manager.set_current_note_file(
                os.path.join(NOTES_FOLDER, selected_note)
            )

            with open(note_manager.get_current_note_file(), "r", encoding="utf-8") as f:
                note_content = f.read()

            if len(note_content) <= 4096:
                await query.message.reply_text(
                    _format_message(
                        MessageType.CALLBACK,
                        CallbackDataText(selected_note, note_content),
                    )
                )
            else:
                with open(note_manager.get_current_note_file(), "rb") as f:
                    await query.message.reply_document(
                        document=f,
                        filename=selected_note,
                        caption=_format_message(
                            MessageType.CALLBACK, CallbackDataFile(selected_note)
                        ),
                    )
            try:
                chat_id = query.message.chat_id
                message_id = query.message.message_id

                # Удаляем сообщение
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                await query.message.reply_text(
                    f"Ошибка при удалении сообщения: {str(e)}"
                )
                logger.error(f"Error in delete_message: {str(e)}")
    except Exception as e:
        await query.message.reply_text(f"Ошибка при выборе заметки: {str(e)}")
        logger.error(f"Error in callback_query: {str(e)}")


async def delete_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /deletenote command"""
    if not is_allowed_user(update):
        return
    try:
        if _check_current_note():
            await update.message.reply_text("Нет активной заметки для удаления.")
            return
        os.remove(note_manager.get_current_note_file())
        note_name = os.path.basename(note_manager.get_current_note_file())
        note_manager.set_current_note_file(None)
        await update.message.reply_text(f"Заметка {note_name} удалена.")

        await list_notes(update, context)
    except Exception as e:
        await update.message.reply_text(f"Ошибка при удалении заметки: {str(e)}")
        logger.error(f"Error in delete_note: {str(e)}")
