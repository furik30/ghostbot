import asyncio
from utils.gemini_api import generate_text
from utils.common import get_multimodal_history, save_draft
from utils.logger import setup_logger
from pyrogram import Client
from config import PROMPTS

logger = setup_logger("ReplyGen")

async def handle_reply_command(client: Client, chat_id: int, args: list, context_note: str = ""):
    logger.info(f"Generating reply for {chat_id} with args: {args}")
    
    await asyncio.sleep(2)
    await save_draft(client, chat_id, "🧠 Читаю переписку...")
    
    msg_count = 5
    level = 2
    extra_prompt = ""

    used_args = 0
    if len(args) > 0 and args[0].isdigit():
        msg_count = int(args[0])
        used_args += 1
        if len(args) > 1 and args[1].isdigit():
            level = int(args[1])
            used_args += 1
    
    if len(args) > used_args:
        extra_prompt = " ".join(args[used_args:])

    history_parts = await get_multimodal_history(client, chat_id, limit=msg_count)
    
    reply_config = PROMPTS.get('reply', {})
    styles = reply_config.get('styles', {})
    system_instruction = reply_config.get('system_instruction', "You are me.")
    selected_style = styles.get(level, styles.get(2, "Normal style"))
    
    final_contents = []
    
    intro_text = (
        f"CONTEXT/MEMORY: {context_note}\n"
        f"REQUIRED STYLE: {selected_style}\n"
        f"USER EXTRA INSTRUCTION: {extra_prompt}\n"
        f"TASK: Write the reply text based on the chat history below (including images/audio).\n"
        f"CHAT HISTORY:"
    )
    final_contents.append(intro_text)
    final_contents.extend(history_parts)

    await asyncio.sleep(2)
    await save_draft(client, chat_id, "🧠 Думаю...")
    
    response = await generate_text(final_contents, system_instruction)
    logger.info("Reply generated successfully")

    await asyncio.sleep(2)
    await save_draft(client, chat_id, response)