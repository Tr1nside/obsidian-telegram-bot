from telegram import Update
from .utils import (
    ContentType,
    format_content,
    TextContentData,
    append_to_note,
    ensure_proper_code_blocks,
)


def append_caption(update: Update):
    caption = update.message.caption_markdown_v2
    caption = ensure_proper_code_blocks(caption)
    if caption:
        formatted_caption = format_content(
            ContentType.CAPTION, TextContentData(caption)
        )
        append_to_note(formatted_caption)
