import asyncio
from utils.gemini_api import generate_text
from utils.common import get_multimodal_history, save_draft, get_user_firstname
from utils.logger import setup_logger
from utils.text_tools import split_text
from pyrogram import Client, enums
from config import PROMPTS, DRAFT_COOLDOWN

logger = setup_logger("FunTools")

async def handle_roast_command(client: Client, chat_id: int, text: str, **kwargs):
    """
    Команда .roast — прожарка чата.
    kwargs: force (bool), reply_to_message_id (int)
    """
    force = kwargs.get('force', False)
    reply_to_id = kwargs.get('reply_to_message_id')

    logger.info(f"Roasting chat {chat_id} (Force={force})")

    # 1. Индикация (только для обычного режима)
    if not force:
        await asyncio.sleep(DRAFT_COOLDOWN)
        await save_draft(client, chat_id, "🔥 Разогреваю гриль...")

    # 2. История
    history_parts = await get_multimodal_history(client, chat_id, limit=15)

    # 3. Подготовка промпта
    user_firstname = await get_user_firstname(client)

    roast_config = PROMPTS.get('roast', {})
    raw_instruction = roast_config.get('system_instruction', "Roast this chat.")
    common_formatting = PROMPTS.get('common_formatting', "")

    system_instruction = raw_instruction.replace("{common_formatting}", common_formatting)
    system_instruction = system_instruction.replace("{user_firstname}", user_firstname)

    final_contents = ["Here is the chat history to roast:", *history_parts]

    if not force:
        await asyncio.sleep(DRAFT_COOLDOWN)
        await save_draft(client, chat_id, "🌶️ Перчу факты...")

    response = await generate_text(final_contents, system_instruction)

    # Отправка
    if not force:
        await save_draft(client, chat_id, "🔥 Прожарка готова!")
        await asyncio.sleep(0.5)

    # Определяем цель отправки
    target_chat = chat_id if force else "me"

    try:
        header = "🔥🔥🔥 **Прожарка** 🔥🔥🔥\n\n"
        full_text = header + response

        chunks = split_text(full_text)
        for i, chunk in enumerate(chunks):
            text_to_send = chunk
            if len(chunks) > 1 and i > 0:
                text_to_send = f"...(часть {i+1})\n{chunk}"

            # Если force и это первый чанк, можно ответить на reply_to_id
            current_reply_to = reply_to_id if (force and i == 0) else None

            await client.send_message(target_chat, text_to_send, parse_mode=enums.ParseMode.MARKDOWN, reply_to_message_id=current_reply_to)
            await asyncio.sleep(0.5)

        if not force:
            await save_draft(client, chat_id, "") # Чистим драфт
    except Exception as e:
        logger.error(f"Failed to send roast: {e}")
        if not force:
            await save_draft(client, chat_id, "❌ Ошибка прожарки")

async def handle_roast_force(client: Client, chat_id: int, text: str, **kwargs):
    """Обертка для .roastf (Force Roast)"""
    kwargs['force'] = True
    await handle_roast_command(client, chat_id, text, **kwargs)

def register(registry):
    registry.register(['.roast'], handle_roast_command, "Прожарка чата")
    registry.register(['.roastf'], handle_roast_force, "Прожарка чата (сразу в чат)")
