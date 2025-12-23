from google import genai
from google.genai import types
import os
import asyncio
from config import GEMINI_API_KEY
from utils.logger import setup_logger

logger = setup_logger("GeminiAPI")

# Инициализация клиента Google GenAI
client = genai.Client(api_key=GEMINI_API_KEY)

# Настройка модели
MODEL_NAME = "gemini-2.0-flash-exp"

async def generate_text(contents, system_instruction: str) -> str:
    """
    Генерирует текст с помощью Google Gemini API (новый SDK).

    Args:
        contents: Список содержимого (строки, словари с медиа).
        system_instruction: Системный промпт.

    Returns:
        Сгенерированный текст ответа.
    """
    try:
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not set")
            return "Ошибка: API ключ не найден."

        # Подготовка контента для нового SDK
        # SDK ожидает список, где каждый элемент может быть строкой или объектом Content
        # Для упрощения мы будем формировать список parts для одного сообщения user
        
        formatted_contents = []
        
        for part in contents:
            if isinstance(part, str):
                formatted_contents.append(part)
            elif isinstance(part, dict):
                # Обработка медиа (inline data)
                # Новый SDK принимает types.Part.from_bytes(data, mime_type)
                mime_type = part.get("mime_type")
                data = part.get("data")
                if mime_type and data:
                    formatted_contents.append(
                        types.Part.from_bytes(data=data, mime_type=mime_type)
                    )

        # Конфигурация генерации
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
        )

        logger.info(f"Sending request to Gemini ({MODEL_NAME})...")

        # Вызов API (асинхронной обертки в SDK пока может не быть, используем run_in_executor если нужно,
        # но google-genai поддерживает async методы, если клиент создан правильно.
        # В версии 0.1+ клиент синхронный, но есть .aio.
        # Проверим документацию: client.aio.models.generate_content

        response = await client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=formatted_contents,
            config=config
        )

        if response.text:
            return response.text
        else:
            logger.warning("Gemini returned empty response.")
            return "Ошибка: Пустой ответ от нейросети."

    except Exception as e:
        logger.error(f"Gemini API Error: {e}", exc_info=True)
        return f"Ошибка API: {e}"
