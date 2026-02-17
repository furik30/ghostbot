import asyncio
import re
from utils.gemini_api import generate_text
from utils.common import save_draft, get_user_firstname
from utils.logger import setup_logger
from pyrogram import Client, enums
from config import PROMPTS, DRAFT_COOLDOWN

logger = setup_logger("TextFixer")

async def handle_fix_command(client: Client, chat_id: int, text: str, **kwargs):
    """
    Обработчик .fix / .ff
    Поддерживает:
    1. Префикс: .fix Текст (text = "Текст")
    2. Инфикс/Постфикс: Текст .fix Инструкция (text = "Текст .fix Инструкция")

    kwargs:
      force (bool): если True, отправляет сразу в чат.
      reply_to_message_id (int): ID сообщения для ответа.
      trigger (str): команда, которая вызвала хендлер (например, .fix или .ff)
    """
    force = kwargs.get('force', False)
    reply_to_id = kwargs.get('reply_to_message_id')
    trigger = kwargs.get('trigger', '.fix') # Default fallback

    # Поиск разделителя в тексте (инфиксный режим)
    # Ищем любую из зарегистрированных команд (.fix, .ff) окруженную пробелами/началом строки
    # Но лучше ориентироваться на trigger, если он передан
    
    # Паттерн: (?:^|\s) + escaped_trigger + (?:$|\s)
    # Но нам нужно именно разделить текст.

    # Попробуем найти trigger внутри текста
    match = None
    if trigger:
        pattern = r"(?:^|\s)" + re.escape(trigger) + r"(?:$|\s)"
        match = re.search(pattern, text)

    # Если не нашли по переданному триггеру, попробуем найти .fix или .ff явно (fallback)
    if not match:
         match = re.search(r"(?:^|\s)(\.(?:fix|ff))(?:$|\s)", text)

    if match:
        # Инфиксный режим: есть разделитель
        # match.start() - начало совпадения (возможно пробел)
        # match.end() - конец совпадения (возможно пробел)
        # Нам нужно найти сам текст команды внутри match

        full_match = match.group(0)
        # command_start внутри match
        if trigger in full_match:
             cmd_str = trigger
        elif ".fix" in full_match:
             cmd_str = ".fix"
        elif ".ff" in full_match:
             cmd_str = ".ff"
        else:
             cmd_str = full_match.strip()

        # Абсолютные координаты команды в тексте
        cmd_start = text.find(cmd_str, match.start())
        cmd_end = cmd_start + len(cmd_str)

        original_text = text[:cmd_start].strip()
        user_instruction = text[cmd_end:].strip()
    else:
        # Префиксный режим (registry уже убрал команду из начала, если она была в начале)
        # Либо это просто текст без инфиксной команды
        original_text = text.strip()
        user_instruction = ""

    logger.info(f"Fixing text (Force={force}). Len: {len(original_text)}. Instr: {user_instruction}")

    # Индикация (только если не Force)
    if not force:
        await asyncio.sleep(DRAFT_COOLDOWN)
        await save_draft(client, chat_id, "🔧 Полирую текст...")

    user_firstname = await get_user_firstname(client)
    fixer_config = PROMPTS.get('text_fixer', {})
    raw_instruction = fixer_config.get('system_instruction', "Fix the text.")

    system_instruction = raw_instruction.replace("{user_firstname}", user_firstname)

    contents = [
        f"Constraint: Do not significantly increase the text length.",
        f"USER INSTRUCTION: {user_instruction}",
        f"---\nInput text: {original_text}"
    ]

    response = await generate_text(contents, system_instruction)

    # Логика отправки
    if len(response) > 4000:
        if force:
             # Если Force и длинный текст, отправляем чанками в чат
             # (хотя для .fix это редкость, но на всякий случай)
             logger.warning("Response too long for single message.")
             # Simple chunking logic handled by caller usually, but here we do it directly
             # Import split_text logic? We don't have it imported.
             # Let's just send first 4000 chars and warn?
             # Or use utils.text_tools.split_text
             from utils.text_tools import split_text
             chunks = split_text(response)
             for i, chunk in enumerate(chunks):
                 await client.send_message(chat_id, chunk, reply_to_message_id=reply_to_id if i==0 else None)
                 await asyncio.sleep(0.5)
        else:
            logger.warning("Response too long, sending to Saved Messages.")
            try:
                await client.send_message("me", f"🔧 **Fixed Text:**\n\n{response}")
                await asyncio.sleep(DRAFT_COOLDOWN)
                await save_draft(client, chat_id, "📦 Результат в Избранном (слишком длинный).")
                await asyncio.sleep(3.0)
                await save_draft(client, chat_id, "")
            except Exception as e:
                logger.error(f"Failed to send to Saved Messages: {e}")
                await save_draft(client, chat_id, "❌ Ошибка размера.")
    else:
        if force:
            # Force: отправляем сразу в чат
            try:
                await client.send_message(chat_id, response, reply_to_message_id=reply_to_id)
            except Exception as e:
                logger.error(f"Failed to send force message: {e}")
        else:
            # Draft: сохраняем в черновик
            await asyncio.sleep(DRAFT_COOLDOWN)
            await save_draft(client, chat_id, response)

async def handle_fix_force(client: Client, chat_id: int, text: str, **kwargs):
    """Обертка для .ff (Force Fix)"""
    kwargs['force'] = True
    kwargs['trigger'] = '.ff'
    await handle_fix_command(client, chat_id, text, **kwargs)

def register(registry):
    registry.register(['.fix'], handle_fix_command, "Исправление текста")
    registry.register(['.ff'], handle_fix_force, "Исправление текста (сразу в чат)")
