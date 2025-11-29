import asyncio
from utils.gemini_api import generate_text
from utils.common import save_draft
from utils.logger import setup_logger
from pyrogram import Client
from config import PROMPTS

logger = setup_logger("PromptBuilder")

async def handle_prompt_command(client: Client, chat_id: int, raw_text: str):
    prefix = ".p " if raw_text.startswith(".p ") else ".prompt "
    user_request = raw_text[len(prefix):].strip()
    
    logger.info(f"Building prompt for: {user_request[:30]}...")

    await asyncio.sleep(2)
    await save_draft(client, chat_id, "✨ Инженeрю промпт...")

    prompt_config = PROMPTS.get('prompt_builder', {})
    system_instruction = prompt_config.get('system_instruction', "Act as a Prompt Engineer.")

    meta_prompt = (
        f"{system_instruction}\n"
        f"User Request: {user_request}\n"
    )

    response = await generate_text(meta_prompt)

    await asyncio.sleep(2)
    await save_draft(client, chat_id, response)