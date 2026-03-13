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
        # загружаем настройки из центрального конфига: секретный ключ для авторизации и идентификатор клиента
        self.auth_key = Config.GIGA_CREDS
        self.client_id = Config.GIGA_CLIENT_ID
        # устанавливаем область доступа и названия моделей: быструю для простых задач и мощную для работы с фото
        self.scope = Config.GIGA_SCOPE
        self.model_lite = Config.GIGA_MODEL_LITE
        self.model_max = Config.GIGA_MODEL_MAX
        # создаем переменные для хранения временного токена и времени когда он перестанет работать
        self.access_token = None
        self.token_expires = 0
        # указываем базовый интернет-адрес серверов сбера для всех последующих обращений к ии
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"

    def _update_token(self):
        """Обновление JWT токена доступа (валиден 30 минут)."""
        # проверяем есть ли у нас уже действующий пропуск и не истекло ли время его годности
        if self.access_token and time.time() < self.token_expires:
            return
            
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        # подготавливаем технический заголовок запроса: указываем тип данных и наш уникальный секретный код
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {self.auth_key}'
        }
        
        try:
            # отправляем запрос на сервер сбера для получения нового временного пароля для работы с ии
            # verify=False нужен, так как у Сбера часто свои сертификаты
            res = requests.post(url, headers=headers, data={'scope': self.scope}, verify=False)
            res.raise_for_status()
            data = res.json()
            # сохраняем полученный код доступа в память приложения
            self.access_token = data['access_token']
            # рассчитываем время завершения работы пропуска в секундах и вычитаем минуту для надежности
            # Уменьшаем время жизни на 60 сек для безопасности
            self.token_expires = (data['expires_at'] / 1000) - 60
        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА ОБНОВЛЕНИЯ ТОКЕНА GIGACHAT: {e}")

    def _optimize_for_ai(self, image_bytes: bytes) -> bytes:
        """Сжатие фото перед отправкой для экономии токенов и ускорения."""
        try:
            # считываем массив байтов фотографии и превращаем его в объект изображения для обработки
            img = Image.open(io.BytesIO(image_bytes))
            # удаляем лишнюю информацию о прозрачности если она есть чтобы успешно сохранить файл в jpeg
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # пропорционально уменьшаем разрешение фото до лимита в 1024 пикселя для экономии токенов
            # Ресайз согласно лимитам в Config
            img.thumbnail((Config.IMAGE_MAX_SIZE, Config.IMAGE_MAX_SIZE), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            # пересохраняем картинку в максимально легкий формат jpeg с качеством семьдесят процентов
            img.save(output, format="JPEG", quality=70)
            return output.getvalue()
        except Exception as e:
            print(f"Ошибка оптимизации изображения: {e}")
            return image_bytes

    def upload_image(self, image_bytes: bytes):
        """Загрузка изображения на сервер Сбера (необходимо для Vision моделей)."""
        # проверяем наличие актуального пропуска в систему перед тем как передавать данные
        self._update_token()
        if not self.access_token: 
            return None

        headers = {
            'Authorization': f'Bearer {self.access_token}', 
            'RqUID': str(uuid.uuid4()),
            'X-Client-ID': self.client_id
        }
        
        # прикрепляем файл и ставим специальную пометку general чтобы ии разрешили его увидеть
        # 'purpose': 'general' обязательно для работы в чате
        files = {
            'file': ('plant.jpg', image_bytes, 'image/jpeg'),
            'purpose': (None, 'general')
        }
        
        try:
            # физически передаем оптимизированное фото в облачное хранилище серверов сбера
            res = requests.post(f"{self.base_url}/files", headers=headers, files=files, verify=False)
            
            if res.status_code != 200:
                print(f"Ошибка загрузки файла в Сбер ({res.status_code}): {res.text}")
                return None
            
            # возвращаем из функции уникальный номер файла по которому ии найдет его в базе
            return res.json().get('id')
        except Exception as e:
            print(f"Сетевая ошибка при загрузке фото: {e}")
            return None
        
    def get_ai_response(self, db: Session, user_id: int, system_prompt: dict, user_text: str, use_max=False, attachments=None, p_type="chat"):
        """Универсальный метод общения с GigaChat."""
        # обновляем авторизацию перед каждым важным запросом к мозгам нейросети
        self._update_token()
        if not self.access_token:
            return None, "Ошибка авторизации (нет токена доступа)."

        # выбираем мощную модель если нужно анализировать картинку или легкую если только текст
        # Выбор модели: Max (для фото) или Lite (для текста)
        model = self.model_max if use_max else self.model_lite
        
        # если мы просим ии вернуть данные для базы ставим минимальную температуру для точности
        # Если промпт требует JSON, понижаем температуру для точности
        is_json = "JSON" in system_prompt.get('content', '')
        
        # формируем полный пакет инструкций: роль нейросети вопрос пользователя и ссылки на фото
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
            # отправляем запрос на генерацию ответа и ждем завершения обработки
            res = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, verify=False)
            
            # проверяем статус ответа чтобы вовремя заметить если у нас кончились деньги на токены
            # Логируем статус ответа (поможет поймать 429 - конец токенов)
            if res.status_code != 200:
                print(f"GigaChat Error ({res.status_code}): {res.text}")
                return None, f"GigaChat вернул ошибку {res.status_code}"

            data = res.json()
            # извлекаем основной текст который придумал ии из вложенной структуры ответа
            raw_content = data['choices'][0]['message']['content']
            # запоминаем сколько виртуальных ресурсов мы потратили на этот конкретный вопрос
            usage = data.get('usage', {}).get('total_tokens', 0)

            # очищаем ответ от лишнего оформления чтобы программа могла превратить его в список или словарь
            # Очистка Markdown-мусора
            clean_content = raw_content.replace("```json", "").replace("```", "").strip()

            # блок записи истории: сохраняем факт консультации и количество токенов в нашу базу данных
            # Логирование расхода в БД
            try:
                consultation = AIConsultation(
                    user_id=user_id,
                    prompt_text=user_text[:300], # пишем только начало вопроса чтобы не раздувать базу
                    response_text=clean_content,
                    consultation_type=p_type
                )
                db.add(consultation)
                # записываем расход токенов в таблицу статистики для последующего анализа затрат
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
        # просим ии превратить простое человеческое название в официальное биологическое имя
        res, err = self.get_ai_response(db, user_id, PROMPT_NORMALIZE, name, p_type="normalize")
        if err: return None, err
        try: return json.loads(res), None
        except: return None, "ИИ вернул некорректный JSON (нормализация)."

    def get_passport_data(self, db: Session, user_id: int, name: str):
        """Генерация характеристик (интервалы полива и т.д.)."""
        # просим ии найти в своей базе знаний интервалы полива и требования к свету для растения
        res, err = self.get_ai_response(db, user_id, PROMPT_GENERATE_PASSPORT, f"Растение: {name}", p_type="passport")
        if err: return None, err
        try: return json.loads(res), None
        except: return None, "ИИ вернул некорректный JSON (паспорт)."

    def ask_agronomist(self, db: Session, user_id: int, plant_info: str, query: str):
        """Текстовый чат с агрономом."""
        # передаем в нейросеть всю информацию о конкретном цветке пользователя чтобы совет был точным
        full_query = f"Контекст: {plant_info}. Вопрос: {query}"
        return self.get_ai_response(db, user_id, PROMPT_AGRONOMIST, full_query, p_type="advice")

    def diagnose_plant(self, db: Session, user_id: int, img: bytes):
        """Диагностика болезней по фото (использует модель Max)."""
        # сначала сжимаем фото затем загружаем его на сервер и получаем номер этого файла
        opt_img = self._optimize_for_ai(img)
        f_id = self.upload_image(opt_img)
        if not f_id: return None, "Не удалось загрузить фото на сервер Сбера."
        # вызываем самую мощную модель для поиска признаков болезней или вредителей на снимке
        return self.get_ai_response(db, user_id, PROMPT_VISION_DIAGNOSIS, "Проанализируй состояние", use_max=True, attachments=[f_id], p_type="diagnosis")

    def identify_plant_photo(self, db: Session, user_id: int, img: bytes):
        """Распознавание вида растения по фото (использует модель Max)."""
        # подготавливаем изображение и передаем его в облако для обработки нейросетью
        opt_img = self._optimize_for_ai(img)
        f_id = self.upload_image(opt_img)
        if not f_id: return None, "Не удалось загрузить фото для анализа."
        
        # запускаем процесс распознавания и просим ии сразу выдать все характеристики вида в формате json
        res, err = self.get_ai_response(db, user_id, PROMPT_IDENTIFY_TO_ADD, "Кто это на фото?", use_max=True, attachments=[f_id], p_type="identify")
        if err: return None, err
        
        try: 
            # превращаем текстовый ответ ии в готовый программный объект со свойствами растения
            return json.loads(res), None
        except Exception as e: 
            print(f"Ошибка парсинга JSON распознавания: {e} | Ответ ИИ: {res}")
            return None, "Не удалось распознать формат данных растения."