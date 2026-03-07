import requests
import uuid
import time
import json
import io
from PIL import Image
from config import Config
from database.models import AIConsultation, TokenUsage
from sqlalchemy.orm import Session
from .prompts import *

class GigaChatService:
    def __init__(self):
        # настройки из центрального курьера
        self.auth_key = Config.GIGA_CREDS
        self.client_id = Config.GIGA_CLIENT_ID
        self.scope = Config.GIGA_SCOPE
        self.model_lite = Config.GIGA_MODEL_LITE
        self.model_max = Config.GIGA_MODEL_MAX
        self.access_token = None
        self.token_expires = 0
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"

    def _update_token(self):
        # обновление jwt токена доступа. 
        # токен живет 30 минут, мы используем защитный интервал в 60 секунд, 
        # чтобы гарантировать стабильность соединения при передаче данных.
        if time.time() < self.token_expires:
            return
            
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {self.auth_key}'
        }
        
        try:
            res = requests.post(url, headers=headers, data={'scope': self.scope}, verify=False)
            res.raise_for_status()
            data = res.json()
            self.access_token = data['access_token']
            self.token_expires = (data['expires_at'] / 1000) - 60
        except Exception as e:
            print(f"ошибка обновления токена: {e}")

    def _optimize_for_ai(self, image_bytes: bytes) -> bytes:
        # сжатие изображения в оперативной памяти перед отправкой в ии. 
        # процесс включает конвертацию в rgb для удаления альфа-каналов, 
        # пропорциональный ресайз до лимитов из конфига и сохранение в jpeg. 
        # это критически важно для экономии токенов и ускорения ответа vision-модели.
        try:
            img = Image.open(io.BytesIO(image_bytes))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            img.thumbnail((Config.IMAGE_MAX_SIZE, Config.IMAGE_MAX_SIZE), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=70)
            return output.getvalue()
        except:
            return image_bytes

    def upload_image(self, image_bytes):
        # процесс загрузки изображения во временное хранилище. 
        # согласно документации опенапи, для использования файла в чате 
        # необходимо передать заголовок X-Client-ID и параметр purpose=general. 
        # использование RqUID позволяет службе поддержки сбера отследить запрос при сбое.
        self._update_token()
        if not self.access_token: 
            return None

        headers = {
            'Authorization': f'Bearer {self.access_token}', 
            'RqUID': str(uuid.uuid4()), # уникальный идентификатор транзакции
            'X-Client-ID': self.client_id
        }
        
        # 'purpose': 'general' — это ключ, открывающий доступ ии к файлу
        files = {
            'file': ('plant.jpg', image_bytes, 'image/jpeg'),
            'purpose': (None, 'general')
        }
        
        try:
            res = requests.post(f"{self.base_url}/files", headers=headers, files=files, verify=False)
            
            # если сбер вернет не 200, мы увидим причину в консоли
            if res.status_code != 200:
                print(f"Технический лог Сбера ({res.status_code}): {res.text}")
                return None
                
            return res.json().get('id')
        except Exception as e:
            print(f"Ошибка сетевого уровня при загрузке фото: {e}")
            return None
        
    def get_ai_response(self, db: Session, user_id: int, system_prompt, user_text, use_max=False, attachments=None, p_type="chat"):
        # универсальный метод получения ответа от модели. 
        # объединяет логику выбора модели (lite/max), автоматическую настройку 
        # температуры для json-промптов и обязательное логирование истории 
        # консультаций и расхода токенов в базу данных.
        self._update_token()
        if not self.access_token:
            return None, "Ошибка авторизации сервиса ИИ."

        model = self.model_max if use_max else self.model_lite
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
            res.raise_for_status()
            data = res.json()
            
            raw_content = data['choices'][0]['message']['content']
            usage = data.get('usage', {}).get('total_tokens', 0)

            # очистка результата от markdown разметки кода
            clean_content = raw_content.replace("```json", "").replace("```", "").strip()

            # атомарное логирование в базу данных
            consultation = AIConsultation(
                user_id=user_id,
                prompt_text=user_text[:300],
                response_text=clean_content,
                consultation_type=p_type
            )
            db.add(consultation)
            db.add(TokenUsage(user_id=user_id, tokens_count=usage, request_type=p_type))
            db.commit()

            return clean_content, None
        except Exception as e:
            db.rollback()
            return None, f"Ошибка работы ИИ: {str(e)}."

    def identify_by_name(self, db: Session, user_id: int, name: str):
        # нормализация названия через PROMPT_NORMALIZE
        res, err = self.get_ai_response(db, user_id, PROMPT_NORMALIZE, name, p_type="normalize")
        if err: return None, err
        try: return json.loads(res), None
        except: return None, "Некорректный формат ответа."

    def get_passport_data(self, db: Session, user_id: int, name: str):
        # генерация технических характеристик растения через ии
        res, err = self.get_ai_response(db, user_id, PROMPT_GENERATE_PASSPORT, f"Растение: {name}", p_type="passport")
        if err: return None, err
        try: return json.loads(res), None
        except: return None, "Не удалось сформировать паспорт."

    def ask_agronomist(self, db: Session, user_id: int, plant_info: str, query: str):
        # быстрая консультация агронома в текстовом чате
        full_query = f"Контекст растения: {plant_info}. Вопрос: {query}"
        return self.get_ai_response(db, user_id, PROMPT_AGRONOMIST, full_query, p_type="advice")

    def diagnose_plant(self, db: Session, user_id: int, img: bytes):
        # визуальная диагностика болезней по фотографии. 
        # перед отправкой байты оптимизируются для минимизации затрат токенов.
        opt_img = self._optimize_for_ai(img)
        f_id = self.upload_image(opt_img)
        if not f_id: return None, "Загрузка изображения не удалась."
        return self.get_ai_response(db, user_id, PROMPT_VISION_DIAGNOSIS, "Что на фото?", use_max=True, attachments=[f_id], p_type="diagnosis")

    def identify_plant_photo(self, db: Session, user_id: int, img: bytes):
        # определение вида растения по фото для добавления в базу. 
        # используется тяжелая модель max для обеспечения точности систематики.
        opt_img = self._optimize_for_ai(img)
        f_id = self.upload_image(opt_img)
        if not f_id: return None, "Загрузка изображения не удалась."
        res, err = self.get_ai_response(db, user_id, PROMPT_IDENTIFY_TO_ADD, "Кто это?", use_max=True, attachments=[f_id], p_type="identify")
        if err: return None, err
        try: return json.loads(res), None
        except: return None, "Не удалось распознать растение."