import os
import uuid
import io
from PIL import Image
from config import Config

class FileService:
    @staticmethod
    def process_and_save(image_bytes: bytes, subfolder: str = "plants") -> str:
        """
        Оптимизирует изображение и сохраняет его в папку assets.
        Возвращает относительный путь для хранения в БД.
        """
        if not image_bytes:
            return None
        
        try:
            # 1. Открываем изображение из байтов
            img = Image.open(io.BytesIO(image_bytes))
            
            # 2. Конвертируем в RGB (убираем прозрачность, если это PNG, для сохранения в JPEG)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # 3. Ресайз под настройки из Config
            img.thumbnail((Config.IMAGE_MAX_SIZE, Config.IMAGE_MAX_SIZE), Image.Resampling.LANCZOS)
            
            # 4. Формируем пути
            # save_dir будет "assets/plants" или "assets/logs"
            save_dir = os.path.join(Config.UPLOAD_DIR, subfolder)
            os.makedirs(save_dir, exist_ok=True)
            
            # Генерируем уникальное имя
            filename = f"{uuid.uuid4()}.jpg"
            
            # Абсолютный путь для физического сохранения на диске
            abs_path = os.path.join(save_dir, filename)
            
            # Путь для базы данных (без префикса assets/)
            # Flet автоматически ищет файлы в папке assets, поэтому в БД пишем только подпапку
            rel_path_for_db = f"{subfolder}/{filename}"
            
            # 5. Сохраняем файл на диск
            img.save(
                abs_path, 
                "JPEG", 
                quality=Config.IMAGE_QUALITY, 
                optimize=True
            )
            
            # Отладка в консоль, чтобы ты видел, куда реально лег файл
            print(f"✅ Файл успешно сохранен: {abs_path}")
            
            return rel_path_for_db 
            
        except Exception as e:
            print(f"❌ Ошибка в FileService при сохранении: {e}")
            return None