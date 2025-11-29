import asyncio
from utils.gemini_api import generate_text
from utils.common import get_recent_history, save_draft
from utils.logger import setup_logger
from pyrogram import Client
from config import PROMPTS, DRAFT_COOLDOWN

logger = setup_logger("MimicryMod")

async def handle_mimicry_command(client: Client, chat_id: int, chat_contexts: dict):
    """
    Логика команды .mimi
    Читает историю + ТЕКУЩУЮ ЗАМЕТКУ -> Создает актуализированный контекст.
    """
    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, "🕵️‍♂️ Составляю досье на собеседника...")
    
    history = await get_recent_history(client, chat_id, limit=100)
    current_memo = chat_contexts.get(str(chat_id), "None")
    
    mimicry_config = PROMPTS.get('mimicry', {})
    system_instruction = mimicry_config.get('system_instruction', "Create a context note.")
    
    prompt = (
        f"{system_instruction}\n"
        f"---\nCURRENT MEMO (Previous knowledge): {current_memo}\n---\n"
        f"CHAT HISTORY:\n{history}\n---\n"
        f"TASK: Update/Create the context note."
    )

    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, "🧠 Формулирую контекст...")
    
    response = await generate_text(prompt)
    clean_response = response.strip().replace("\n", " ")
    logger.info(f"Generated context for {chat_id}")
    command_to_show = f".memo {clean_response}"
    
    await asyncio.sleep(1.0)
    await save_draft(client, chat_id, command_to_show)