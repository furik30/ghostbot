import asyncio
from utils.gemini_api import generate_text
from utils.common import save_draft, get_user_firstname
from utils.logger import setup_logger
from pyrogram import Client
from config import PROMPTS, DRAFT_COOLDOWN

logger = setup_logger("PromptBuilder")

async def handle_prompt_command(client: Client, chat_id: int, text: str, **kwargs):
    """
    Обработчик .p / .prompt
    text: сам запрос пользователя
    """
    user_request = text.strip()
    
    logger.info(f"Building prompt for: {user_request[:30]}...")

    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, "✨ Инженeрю промпт...")

    user_firstname = await get_user_firstname(client)
    prompt_config = PROMPTS.get('prompt_builder', {})
    raw_instruction = prompt_config.get('system_instruction', "Act as a Prompt Engineer.")

    system_instruction = raw_instruction.replace("{user_firstname}", user_firstname)

    contents = [
        f"User Request: {user_request}"
    ]

    response = await generate_text(contents, system_instruction)

    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, response)

def register(registry):
    registry.register(['.p', '.prompt'], handle_prompt_command, "Prompt Engineering")
