import requests
import uuid
import time
import json
import io
from PIL import Image
from sqlalchemy.orm import Session

from config import Config
from database.models import AIConsultation, TokenUsage
from .prompts import *

class GigaChatService:
    def __init__(self):
        # Настройки из центрального конфига
        self.auth_key = Config.GIGA_CREDS
        self.client_id = Config.GIGA_CLIENT_ID
        self.scope = Config.GIGA_SCOPE
        self.model_lite = Config.GIGA_MODEL_LITE
        self.model_max = Config.GIGA_MODEL_MAX
        self.access_token = None
        self.token_expires = 0
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"

    def _update_token(self):
        """Обновление JWT токена доступа (валиден 30 минут)."""
        if self.access_token and time.time() < self.token_expires:
            return
            
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {self.auth_key}'
        }
        
        try:
            # verify=False нужен, так как у Сбера часто свои сертификаты
            res = requests.post(url, headers=headers, data={'scope': self.scope}, verify=False)
            res.raise_for_status()
            data = res.json()
            self.access_token = data['access_token']
            # Уменьшаем время жизни на 60 сек для безопасности
            self.token_expires = (data['expires_at'] / 1000) - 60
        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА ОБНОВЛЕНИЯ ТОКЕНА GIGACHAT: {e}")

    def _optimize_for_ai(self, image_bytes: bytes) -> bytes:
        """Сжатие фото перед отправкой для экономии токенов и ускорения."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Ресайз согласно лимитам в Config
            img.thumbnail((Config.IMAGE_MAX_SIZE, Config.IMAGE_MAX_SIZE), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=70)
            return output.getvalue()
        except Exception as e:
            print(f"Ошибка оптимизации изображения: {e}")
            return image_bytes

    def upload_image(self, image_bytes: bytes):
        """Загрузка изображения на сервер Сбера (необходимо для Vision моделей)."""
        self._update_token()
        if not self.access_token: 
            return None

        headers = {
            'Authorization': f'Bearer {self.access_token}', 
            'RqUID': str(uuid.uuid4()),
            'X-Client-ID': self.client_id
        }
        
        # 'purpose': 'general' обязательно для работы в чате
        files = {
            'file': ('plant.jpg', image_bytes, 'image/jpeg'),
            'purpose': (None, 'general')
        }
        
        try:
            res = requests.post(f"{self.base_url}/files", headers=headers, files=files, verify=False)
            
            if res.status_code != 200:
                print(f"Ошибка загрузки файла в Сбер ({res.status_code}): {res.text}")
                return None
                
            return res.json().get('id')
        except Exception as e:
            print(f"Сетевая ошибка при загрузке фото: {e}")
            return None
        
    def get_ai_response(self, db: Session, user_id: int, system_prompt: dict, user_text: str, use_max=False, attachments=None, p_type="chat"):
        """Универсальный метод общения с GigaChat."""
        self._update_token()
        if not self.access_token:
            return None, "Ошибка авторизации (нет токена доступа)."

        # Выбор модели: Max (для фото) или Lite (для текста)
        model = self.model_max if use_max else self.model_lite
        
        # Если промпт требует JSON, понижаем температуру для точности
        is_json = "JSON" in system_prompt.get('content', '')
        
        payload = {
            "model": model,
            "messages": [
                system_prompt, 
                {"role": "user", "content": user_text, "attachments": attachments or []}
            ],
            "temperature": 0.1 if is_json else 0.7
        }
        
        headers = {
            'Authorization': f'Bearer {self.access_token}', 
            'Content-Type': 'application/json',
            'X-Client-ID': self.client_id
        }
        
        try:
            res = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, verify=False)
            
            # Логируем статус ответа (поможет поймать 429 - конец токенов)
            if res.status_code != 200:
                print(f"GigaChat Error ({res.status_code}): {res.text}")
                return None, f"GigaChat вернул ошибку {res.status_code}"

            data = res.json()
            raw_content = data['choices'][0]['message']['content']
            usage = data.get('usage', {}).get('total_tokens', 0)

            # Очистка Markdown-мусора
            clean_content = raw_content.replace("```json", "").replace("```", "").strip()

            # Логирование расхода в БД
            try:
                consultation = AIConsultation(
                    user_id=user_id,
                    prompt_text=user_text[:300],
                    response_text=clean_content,
                    consultation_type=p_type
                )
                db.add(consultation)
                db.add(TokenUsage(user_id=user_id, tokens_count=usage, request_type=p_type))
                db.commit()
            except Exception as db_e:
                print(f"Ошибка сохранения логов в БД: {db_e}")
                db.rollback()

            return clean_content, None

        except Exception as e:
            print(f"Ошибка запроса к ИИ: {e}")
            return None, f"Ошибка сети ИИ: {str(e)}"

    def identify_by_name(self, db: Session, user_id: int, name: str):
        """Нормализация названия растения."""
        res, err = self.get_ai_response(db, user_id, PROMPT_NORMALIZE, name, p_type="normalize")
        if err: return None, err
        try: return json.loads(res), None
        except: return None, "ИИ вернул некорректный JSON (нормализация)."

    def get_passport_data(self, db: Session, user_id: int, name: str):
        """Генерация характеристик (интервалы полива и т.д.)."""
        res, err = self.get_ai_response(db, user_id, PROMPT_GENERATE_PASSPORT, f"Растение: {name}", p_type="passport")
        if err: return None, err
        try: return json.loads(res), None
        except: return None, "ИИ вернул некорректный JSON (паспорт)."

    def ask_agronomist(self, db: Session, user_id: int, plant_info: str, query: str):
        """Текстовый чат с агрономом."""
        full_query = f"Контекст: {plant_info}. Вопрос: {query}"
        return self.get_ai_response(db, user_id, PROMPT_AGRONOMIST, full_query, p_type="advice")

    def diagnose_plant(self, db: Session, user_id: int, img: bytes):
        """Диагностика болезней по фото (использует модель Max)."""
        opt_img = self._optimize_for_ai(img)
        f_id = self.upload_image(opt_img)
        if not f_id: return None, "Не удалось загрузить фото на сервер Сбера."
        return self.get_ai_response(db, user_id, PROMPT_VISION_DIAGNOSIS, "Проанализируй состояние", use_max=True, attachments=[f_id], p_type="diagnosis")

    def identify_plant_photo(self, db: Session, user_id: int, img: bytes):
        """Распознавание вида растения по фото (использует модель Max)."""
        opt_img = self._optimize_for_ai(img)
        f_id = self.upload_image(opt_img)
        if not f_id: return None, "Не удалось загрузить фото для анализа."
        
        res, err = self.get_ai_response(db, user_id, PROMPT_IDENTIFY_TO_ADD, "Кто это на фото?", use_max=True, attachments=[f_id], p_type="identify")
        if err: return None, err
        
        try: 
            return json.loads(res), None
        except Exception as e: 
            print(f"Ошибка парсинга JSON распознавания: {e} | Ответ ИИ: {res}")
            return None, "Не удалось распознать формат данных растения."