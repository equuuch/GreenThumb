import requests
import uuid
import time
import json
from config import Config
from database.models import AIConsultation, TokenUsage
from sqlalchemy.orm import Session
from .prompts import *

class GigaChatService:
    def __init__(self):
        # настройки из курьера (config.py)
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
        # согласно документации, токен живет 30 минут. мы используем 
        # защитный интервал в 60 секунд, чтобы предотвратить обрыв 
        # соединения при передаче тяжелых изображений.
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
            print(f"Ошибка обновления токена: {e}")

    def upload_image(self, image_bytes):
        # загрузка фотографии в хранилище сбера. 
        # для анализа фото (vision) необходимо сначала отправить файл 
        # и получить его идентификатор, который затем передается в массив attachments.
        self._update_token()
        if not self.access_token: return None

        headers = {
            'Authorization': f'Bearer {self.access_token}', 
            'RqUID': str(uuid.uuid4()),
            'X-Client-ID': self.client_id
        }
        files = {'file': ('plant.jpg', image_bytes, 'image/jpeg')}
        
        try:
            res = requests.post(f"{self.base_url}/files", headers=headers, files=files, verify=False)
            return res.json().get('id')
        except Exception as e:
            print(f"Ошибка загрузки фото: {e}")
            return None

    def get_ai_response(self, db: Session, user_id: int, system_prompt, user_text, use_max=False, attachments=None, p_type="chat"):
        # универсальный метод получения ответа от ии. 
        # включает автоматическую регулировку температуры (0.1 для json-промптов), 
        # очистку от markdown-разметки и обязательную запись в базу данных 
        # информации о потраченных токенах и сути консультации.
        self._update_token()
        if not self.access_token:
            return None, "Ошибка авторизации сервиса ИИ."

        model = self.model_max if use_max else self.model_lite
        
        # определяем режим json по содержанию промпта (0.1 шоб мусора не было)
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

            # очистка json от блоков кода markdown
            clean_content = raw_content.replace("```json", "").replace("```", "").strip()

            # атомарное логирование консультации
            consultation = AIConsultation(
                user_id=user_id,
                prompt_text=user_text[:300],
                response_text=clean_content,
                consultation_type=p_type
            )
            db.add(consultation)
            db.add(TokenUsage(user_id=user_id, tokens_spent=usage))
            db.commit()

            return clean_content, None
        except Exception as e:
            db.rollback()
            return None, f"Ошибка работы ИИ: {str(e)}."

    # МЕТОДЫ ДЛЯ ФРОНТЕНДА ЕШКИН КОТ

    def identify_by_name(self, db: Session, user_id: int, name: str):
        # нормализация названия через PROMPT_NORMALIZE
        res, err = self.get_ai_response(db, user_id, PROMPT_NORMALIZE, name, p_type="normalize")
        if err: return None, err
        try: return json.loads(res), None
        except: return None, "Некорректный формат ответа."

    def get_passport_data(self, db: Session, user_id: int, name: str):
        # генерация характеристик через генератор паспорта
        res, err = self.get_ai_response(db, user_id, PROMPT_GENERATE_PASSPORT, f"Растение: {name}", p_type="passport")
        if err: return None, err
        try: return json.loads(res), None
        except: return None, "Не удалось сформировать паспорт."

    def ask_agronomist(self, db: Session, user_id: int, plant_info: str, query: str): # --ФАСТ СОВЕТ В ЧАТЕ--
        # быстрый совет по уходу через 
        full_query = f"Контекст растения: {plant_info}. Вопрос: {query}"
        return self.get_ai_response(db, user_id, PROMPT_AGRONOMIST, full_query, p_type="advice")

    def diagnose_plant(self, db: Session, user_id: int, img: bytes): # --ВИЗУАЛЬНАЯ ДИАГНОСТИКА БОЛЕЗНЕЙ--
        # диагностика болезней по фото 
        f_id = self.upload_image(img)
        if not f_id: return None, "Загрузка изображения не удалась."
        return self.get_ai_response(db, user_id, PROMPT_VISION_DIAGNOSIS, "Что на фото?", use_max=True, attachments=[f_id], p_type="diagnosis")

    def identify_plant_photo(self, db: Session, user_id: int, img: bytes):
        # определение вида для базы 
        f_id = self.upload_image(img)
        if not f_id: return None, "Загрузка изображения не удалась."
        res, err = self.get_ai_response(db, user_id, PROMPT_IDENTIFY_TO_ADD, "Кто это?", use_max=True, attachments=[f_id], p_type="identify")
        if err: return None, err
        try: return json.loads(res), None
        except: return None, "Не удалось распознать растение."