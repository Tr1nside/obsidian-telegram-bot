# Obsidian Telegram Bot
Telegram-бот для создания, управления и хранения заметок в формате Markdown, интегрированный с локальной папкой заметок.

## Возможности

- Создание новых заметок в формате `.md` (`/newnote`).
- Просмотр списка всех заметок (`/listnotes`).
- Отображение содержимого текущей заметки (`/printnote`).
- Удаление текущей заметки (`/deletenote`).
- Ограничение доступа к боту по `ALLOWED_USER_ID`.
- Запись отправленных пользователем сообщений в выбранную заметку.

## Требования

- Python 3.10 или выше.
- Telegram-аккаунт и токен бота от [BotFather](https://t.me/BotFather).
- Установленные зависимости:
	- ffmpeg>=1.4,
	- openai-whisper>=20240930,
	- pydub>=0.25.1,
	- python-dotenv>=1.1.0,
	- python-telegram-bot>=22.0,
	- requests>=2.32.3,
	- whisper>=1.1.10,
### Установка FFmpeg 
- **Windows**: Скачайте FFmpeg с [официального сайта](https://ffmpeg.org/download.html) и добавьте его в PATH.
- **Linux**: Установите через пакетный менеджер, например: 
```bash 
sudo apt-get install ffmpeg
```
- **macOS**: Установите через Homebrew:
```bash
brew install ffmpeg
```
## Установка 
1. **Клонируйте репозиторий**: 
	```bash
git clone https://github.com/Tr1nside/obsidian_bd.git
	```
2. **Создайте виртуальное окружение** (рекомендуется): 
	```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

3. Установите зависимости:
	```bash
pip install -r requirements.txt
```
4. Создайте файл .env в корне проекта:
```env
TELEGRAM_TOKEN=YourToken

ALLOWED_USER_ID=YourId

OBSIDIAN_VAULT_PATH="./vault"
NOTES_FOLDER="./vault/notes"
PHOTOS_FOLDER="./vault/cache"
AUDIO_TEMP_FOLDER="./vault/cache/audio"

```
- TELEGRAM_TOKEN: Получите у [BotFather](https://t.me/BotFather).
- ALLOWED_USER_ID: Ваш Telegram ID (узнайте через команду /start).
- OBSIDIAN_VAULT_PATH: Путь к вашему хранилищу Obsidian
- NOTES_FOLDER: Путь к папке для хранения заметок 
- PHOTOS_FOLDER: Путь к папке для хранения фотографий.
- AUDIO_TEMP_FOLDER: Путь для временных файлов.

5. Запустите бота
	```bash
python app/main.py
	```

## Использование 
1. Запустите бота и отправьте команду `/start`, чтобы получить ваш `user_id`. 
2. Добавьте `user_id` в `ALLOWED_USER_ID` в `.env`. 
3. Используйте команды: 
	- `/newnote` — создать новую заметку. 
	- `/listnotes` — показать список заметок. 
	- `/printnote` — вывести текущую заметку. 
	- `/deletenote` — удалить текущую заметку.

## Документация
- [Design Document](https://github.com/Tr1nside/obsidian-telegram-bot/blob/main/docs/design.md) — Архитектура и структура бота.
- [Architecture Decision Records](https://github.com/Tr1nside/obsidian-telegram-bot/blob/main/docs/adr/) — Ключевые решения

## Лицензия

Распространяется под лицензией MIT. См. [LICENSE](https://github.com/Tr1nside/obsidian-telegram-bot/blob/main/LICENSE).

- Создание новых заметок в формате `.md` (`/newnote`).
- Просмотр списка всех заметок (`/listnotes`).
- Отображение содержимого текущей заметки (`/printnote`).
- Удаление текущей заметки (`/deletenote`).
- Ограничение доступа к боту по `ALLOWED_USER_ID`.
- Запись отправленных пользователем сообщений в выбранную заметку.

## Требования

- Python 3.10 или выше.
- Telegram-аккаунт и токен бота от [BotFather](https://t.me/BotFather).
- Установленные зависимости:
	- ffmpeg>=1.4,
	- openai-whisper>=20240930,
	- pydub>=0.25.1,
	- python-dotenv>=1.1.0,
	- python-telegram-bot>=22.0,
	- requests>=2.32.3,
	- whisper>=1.1.10,
### Установка FFmpeg 
- **Windows**: Скачайте FFmpeg с [официального сайта](https://ffmpeg.org/download.html) и добавьте его в PATH.
- **Linux**: Установите через пакетный менеджер, например: 
```bash 
sudo apt-get install ffmpeg
```
- **macOS**: Установите через Homebrew:
```bash
brew install ffmpeg
```
## Установка 
1. **Клонируйте репозиторий**: 
	```bash
git clone https://github.com/Tr1nside/obsidian_bd.git
	```
2. **Создайте виртуальное окружение** (рекомендуется): 
	```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

3. Установите зависимости:
	```bash
pip install -r requirements.txt
```
4. Создайте файл .env в корне проекта:
```env
TELEGRAM_TOKEN=YourToken

ALLOWED_USER_ID=YourId

OBSIDIAN_VAULT_PATH="./vault"
NOTES_FOLDER="./vault/notes"
PHOTOS_FOLDER="./vault/cache"
AUDIO_TEMP_FOLDER="./vault/cache/audio"

```
- TELEGRAM_TOKEN: Получите у [BotFather](https://t.me/BotFather).
- ALLOWED_USER_ID: Ваш Telegram ID (узнайте через команду /start).
- OBSIDIAN_VAULT_PATH: Путь к вашему хранилищу Obsidian
- NOTES_FOLDER: Путь к папке для хранения заметок 
- PHOTOS_FOLDER: Путь к папке для хранения фотографий.
- AUDIO_TEMP_FOLDER: Путь для временных файлов.

5. Запустите бота
	```bash
python app/main.py
	```

## Использование 
1. Запустите бота и отправьте команду `/start`, чтобы получить ваш `user_id`. 
2. Добавьте `user_id` в `ALLOWED_USER_ID` в `.env`. 
3. Используйте команды: 
	- `/newnote` — создать новую заметку. 
	- `/listnotes` — показать список заметок. 
	- `/printnote` — вывести текущую заметку. 
	- `/deletenote` — удалить текущую заметку.

## Документация
- [Design Document](https://github.com/Tr1nside/obsidian-telegram-bot/blob/main/docs/design.md) — Архитектура и структура бота.
- [Architecture Decision Records](https://github.com/Tr1nside/obsidian-telegram-bot/blob/main/docs/adr/) — Ключевые решения

## Лицензия

Распространяется под лицензией MIT. См. [LICENSE](https://github.com/Tr1nside/obsidian-telegram-bot/blob/main/LICENSE).
