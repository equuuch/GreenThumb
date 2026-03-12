import os
import uuid
import io
from PIL import Image
from config import Config

class FileService:
    @staticmethod
    def process_and_save(image_bytes: bytes, subfolder: str = "plants") -> str:
        if not image_bytes:
            return None
        
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            img.thumbnail((Config.IMAGE_MAX_SIZE, Config.IMAGE_MAX_SIZE), Image.Resampling.LANCZOS)
            
            # Для создания папок на диске используем системные пути
            save_dir = os.path.join(Config.UPLOAD_DIR, subfolder)
            os.makedirs(save_dir, exist_ok=True)
            
            filename = f"{uuid.uuid4()}.jpg"
            
            # А вот для базы данных ВСЕГДА используем прямой слэш /
            rel_path_for_db = f"{subfolder}/{filename}"
            
            # Абсолютный путь для сохранения файла на диске
            abs_path = os.path.join(Config.UPLOAD_DIR, subfolder, filename)
            
            img.save(abs_path, "JPEG", quality=Config.IMAGE_QUALITY, optimize=True)
            
            return rel_path_for_db 
        except Exception as e:
            print(f"Ошибка сохранения файла: {e}")
            return None