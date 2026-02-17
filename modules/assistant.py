import asyncio
from utils.gemini_api import generate_text
from utils.common import get_multimodal_history, save_draft, get_user_firstname
from utils.logger import setup_logger
from utils.text_tools import split_text
from pyrogram import Client, enums
from config import PROMPTS, DRAFT_COOLDOWN

logger = setup_logger("Assistant")

async def handle_ask_command(client: Client, chat_id: int, text: str, **kwargs):
    """
    Обработчик для команд .ask / .askf
    text: аргументы (число + вопрос ИЛИ просто вопрос)
    kwargs: force (bool), reply_to_message_id (int)
    """
    force = kwargs.get('force', False)
    reply_to_id = kwargs.get('reply_to_message_id')

    logger.info(f"Assistant request for {chat_id} (Force={force}). Text: {text[:50]}...")

    # Парсинг аргументов
    args = text.split()
    msg_count = 0
    prompt = text

    if len(args) > 0 and args[0].isdigit():
        val = int(args[0])
        # Если число <= 100, считаем его количеством сообщений контекста
        if val <= 100:
            msg_count = val
            prompt = " ".join(args[1:])
        else:
            # Иначе это часть текста (например "2024 год")
            msg_count = 0
            prompt = text

    # Индикация
    if not force:
        await asyncio.sleep(DRAFT_COOLDOWN)
        status_msg = "🧠 Анализирую контекст..." if msg_count > 0 else "🧠 Думаю..."
        await save_draft(client, chat_id, status_msg)

    # Получение контекста (если нужно)
    history_parts = []
    if msg_count > 0:
        history_parts = await get_multimodal_history(client, chat_id, limit=msg_count)

    # Подготовка промпта
    user_firstname = await get_user_firstname(client)
    assistant_config = PROMPTS.get('assistant', {})
    raw_instruction = assistant_config.get('system_instruction', "You are a helpful AI assistant.")

    common_formatting = PROMPTS.get('common_formatting', "")
    system_instruction = raw_instruction.replace("{common_formatting}", common_formatting)
    # Заменяем имя, если оно используется в промпте
    system_instruction = system_instruction.replace("{user_firstname}", user_firstname)

    final_contents = []

    if msg_count > 0:
        final_contents.append("CHAT CONTEXT:")
        final_contents.extend(history_parts)
        final_contents.append("---\n")

    final_contents.append(f"USER REQUEST: {prompt}")

    # Генерация
    response = await generate_text(final_contents, system_instruction)

    # Обработка ответа
    if force:
        # Добавляем подпись для .askf (только в конце последнего чанка, если чанкинг, или просто в текст)
        # Если чанкинг, подпись логично добавить в конец текста ПЕРЕД разбивкой или в последний чанк.
        # Лучше перед разбивкой.

        signature = "\n\n🤖 *Ответ нейросети*"
        full_response = response + signature

        try:
            # Используем split_text для разбивки длинных сообщений
            chunks = split_text(full_response)

            for i, chunk in enumerate(chunks):
                # Reply только на первое сообщение
                current_reply_to = reply_to_id if i == 0 else None
                await client.send_message(chat_id, chunk, parse_mode=enums.ParseMode.MARKDOWN, reply_to_message_id=current_reply_to)
                if len(chunks) > 1:
                    await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Failed to send assistant response: {e}")
    else:
        # Для обычного .ask просто сохраняем в черновик (без подписи)
        # Draft handling usually doesn't need chunking (Telegram client handles it? Or just fails if too long?)
        # Draft length limit is similar to message limit.
        # But split draft is weird. Just save first part or try full.
        await asyncio.sleep(DRAFT_COOLDOWN)
        await save_draft(client, chat_id, response)

async def handle_ask_force(client: Client, chat_id: int, text: str, **kwargs):
    """Обертка для .askf (Force Ask)"""
    kwargs['force'] = True
    await handle_ask_command(client, chat_id, text, **kwargs)

def register(registry):
    registry.register(['.ask'], handle_ask_command, "AI Ассистент (в черновик)")
    registry.register(['.askf'], handle_ask_force, "AI Ассистент (сразу в чат)")
