from moviepy.editor import VideoFileClip
from PIL import Image
import numpy as np


def mp4_to_gif(input_path, output_path, fps=80, scale=0.5):
    # Загружаем видео
    clip = VideoFileClip(input_path)

    # Получаем новые размеры
    new_width = int(clip.w * scale)
    new_height = int(clip.h * scale)

    # Функция для изменения размера кадра
    def resize_frame(frame):
        # Преобразуем кадр в PIL Image
        pil_image = Image.fromarray(frame)
        # Изменяем размер с использованием LANCZOS
        resized_image = pil_image.resize(
            (new_width, new_height), Image.Resampling.LANCZOS
        )
        # Возвращаем кадр как массив numpy
        return np.array(resized_image)

    # Применяем изменение размера к видео
    resized_clip = clip.fl_image(resize_frame)

    # Конвертируем в GIF
    resized_clip.write_gif(output_path, fps=fps)

    # Закрываем клип
    clip.close()
    resized_clip.close()


# Пример использования
mp4_to_gif("input.mp4", "output.gif", fps=10, scale=0.5)
