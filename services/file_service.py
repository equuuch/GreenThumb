import os
import uuid
import io
from PIL import Image
from config import Config

class FileService:
    @staticmethod
    def process_and_save(image_bytes: bytes, subfolder: str = "plants") -> str:
        # оптимизация изображения для экономии токенов и места. 
        # метод конвертирует фото в RGB, делает ресайз согласно Config 
        # и сохраняет в assets/uploads. возвращает относительный путь для бд.
        if not image_bytes:
            return None
        
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # ресайз с сохранением пропорций
            img.thumbnail((Config.IMAGE_MAX_SIZE, Config.IMAGE_MAX_SIZE), Image.Resampling.LANCZOS)
            
            # создание папок
            base_path = os.path.join(Config.UPLOAD_DIR, subfolder)
            if not os.path.exists(base_path):
                os.makedirs(base_path, exist_ok=True)
            
            filename = f"{uuid.uuid4()}.jpg"
            rel_path = os.path.join(subfolder, filename)
            abs_path = os.path.join(Config.UPLOAD_DIR, rel_path)
            
            img.save(abs_path, "JPEG", quality=Config.IMAGE_QUALITY, optimize=True)
            return rel_path 
        except Exception as e:
            print(f"Ошибка сохранения файла: {e}")
            return None