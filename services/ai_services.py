import requests
import uuid
import time
import os
import json
from dotenv import load_dotenv
from .prompts import *

load_dotenv()

class GigaChatService:
    def __init__(self):
        # конфиги из окружения
        self.auth_key = os.getenv("GIGACHAT_CREDENTIALS")
        self.client_id = os.getenv("GIGACHAT_CLIENT_ID")
        self.scope = os.getenv("GIGACHAT_SCOPE")
        self.model_lite = os.getenv("GIGACHAT_MODEL_LITE")
        self.model_max = os.getenv("GIGACHAT_MODEL_MAX")
        self.access_token = None
        self.token_expires = 0
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"

    # получение и обновление токена
    def _update_token(self):
        if time.time() < self.token_expires:
            return
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {self.auth_key}'
        }
        res = requests.post(url, headers=headers, data={'scope': self.scope}, verify=False)
        data = res.json()
        self.access_token = data['access_token']
        self.token_expires = (data['expires_at'] / 1000) - 60

    # загрузка изображения в сбер
    def upload_image(self, image_bytes):
        self._update_token()
        headers = {
            'Authorization': f'Bearer {self.access_token}', 
            'RqUID': str(uuid.uuid4()),
            'X-Client-ID': self.client_id
        }
        files = {'file': ('plant.jpg', image_bytes, 'image/jpeg')}
        res = requests.post(f"{self.base_url}/files", headers=headers, files=files, verify=False)
        return res.json()['id']

    # запрос к ии с очисткой json
    def get_ai_response(self, system_prompt, user_text, use_max=False, attachments=None):
        self._update_token()
        model = self.model_max if use_max else self.model_lite
        payload = {
            "model": model,
            "messages": [system_prompt, {"role": "user", "content": user_text, "attachments": attachments or []}],
            "temperature": 0.1
        }
        headers = {
            'Authorization': f'Bearer {self.access_token}', 
            'Content-Type': 'application/json',
            'X-Client-ID': self.client_id
        }
        res = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, verify=False)
        raw = res.json()['choices'][0]['message']['content']
        return raw.replace("```json", "").replace("```", "").strip()