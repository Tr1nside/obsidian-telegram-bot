from .text import handle_text
from .photo import handle_photo
from .voice import handle_voice
from .video import handle_video
from .animation import handle_animation
from .sticker import handle_sticker

__all__ = [
    "handle_text",
    "handle_photo",
    "handle_voice",
    "handle_video",
    "handle_animation",
    "handle_sticker",
]
