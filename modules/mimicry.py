import asyncio
from utils.gemini_api import generate_text
from utils.common import get_recent_history, save_draft, get_user_firstname
from utils.logger import setup_logger
from pyrogram import Client
from config import PROMPTS, DRAFT_COOLDOWN

logger = setup_logger("MimicryMod")

async def handle_mimicry_command(client: Client, chat_id: int, text: str, **kwargs):
    """
    Логика команды .mimi
    Читает историю + ТЕКУЩУЮ ЗАМЕТКУ -> Создает актуализированный контекст.
    """
    chat_contexts = kwargs.get("chat_contexts", {})

    # Парсинг лимита
    args = text.split()
    limit = 100
    if args and args[0].isdigit():
        limit = int(args[0])

    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, "🕵️‍♂️ Составляю досье на собеседника...")
    
    history = await get_recent_history(client, chat_id, limit=limit)
    current_memo = chat_contexts.get(str(chat_id), "None")
    
    user_firstname = await get_user_firstname(client)
    mimicry_config = PROMPTS.get('mimicry', {})
    raw_instruction = mimicry_config.get('system_instruction', "Create a context note.")

    system_instruction = raw_instruction.replace("{user_firstname}", user_firstname)
    
    contents = [
        f"CURRENT MEMO (Previous knowledge): {current_memo}",
        f"CHAT HISTORY:\n{history}",
        f"TASK: Update/Create the context note."
    ]

    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, "🧠 Формулирую контекст...")
    
    response = await generate_text(contents, system_instruction)

    clean_response = response.strip().replace("\n", " ")
    logger.info(f"Generated context for {chat_id}")
    command_to_show = f".memo {clean_response}"
    
    await asyncio.sleep(1.0)
    await save_draft(client, chat_id, command_to_show)

def register(registry):
    registry.register(['.mimi'], handle_mimicry_command, "Создать досье")
