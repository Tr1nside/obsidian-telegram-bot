from telegram import Update
from telegram.ext import (
    ContextTypes,
)
from config import (
    logger,
)
from .utils import (
    is_allowed_user,
    append_to_note,
    format_content,
    ContentType,
    LocationData,
    main_decorator
)
import requests


async def _get_address_from_coordinates(latitude: float, longitude: float) -> str:
    """Преобразует координаты в читаемый адрес с помощью Nominatim API."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={latitude}&lon={longitude}&format=json"
        headers = {
            "User-Agent": "obsidian_bot/1.0 (petya.08.tomsk@gmail.com)"  # Укажите свой User-Agent
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()
        return data.get("display_name", "Адрес не найден")
    except Exception as e:
        logger.error(f"Ошибка при геокодировании: {str(e)}")
        return "Не удалось получить адрес"

@main_decorator
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function to handle location message. Add location to current note"""
    if not is_allowed_user(update):
        return
    
    
    try:
        location = update.message.location
        latitude = location.latitude
        longitude = location.longitude

        adress = await _get_address_from_coordinates(latitude, longitude)

        # Форматируем данные локации
        markdown_link = format_content(
            ContentType.LOCATION, LocationData(adress)
        )
        append_to_note(markdown_link)
        await update.message.reply_text(
            "Геопозиция добавлена в заметку. #location"
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка при добавлении геопозиции: {str(e)}")
        logger.error(f"Error in handle_location: {str(e)}")
