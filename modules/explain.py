import asyncio
import re
from utils.gemini_api import generate_text
from utils.common import get_multimodal_history, save_draft, get_user_firstname
from utils.logger import setup_logger
from utils.text_tools import clean_html, split_text
from pyrogram import Client, enums
from config import PROMPTS, DRAFT_COOLDOWN

logger = setup_logger("ExplainMod")

async def handle_explain_command(client: Client, chat_id: int, text: str, **kwargs):
    """
    Обработчик .e / .explain
    """
    context_note = kwargs.get("context_note", "")
    args = text.split()

    msg_count = 10
    if len(args) > 0 and args[0].isdigit():
        msg_count = int(args[0])
    
    logger.info(f"Explaining context for {chat_id} (limit: {msg_count})")

    # 1. Индикация
    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, "🕵️‍♂️ Читаю мысли собеседника...")
    
    # 2. Сбор мультимодальной истории
    history_parts = await get_multimodal_history(client, chat_id, limit=msg_count)
    
    # 3. Подготовка промпта
    user_firstname = await get_user_firstname(client)
    explain_config = PROMPTS.get('explain', {})

    raw_instruction = explain_config.get('system_instruction', "Analyze chat.")
    common_formatting = PROMPTS.get('common_formatting', "")

    # Подставляем форматирование и имя
    system_instruction = raw_instruction.replace("{common_formatting}", common_formatting)
    system_instruction = system_instruction.replace("{user_firstname}", user_firstname)
    
    final_contents = []
    intro_text = (
        f"Constraint: Keep the analysis structured and concise.\n"
        f"CONTEXT NOTES: {context_note}\n"
        f"TASK: Provide summary, psychological analysis, and advice. CONSIDER AUDIO AND IMAGES in history.\n"
        f"CHAT HISTORY:"
    )
    final_contents.append(intro_text)
    final_contents.extend(history_parts)

    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, "🧠 Генерирую психопортрет...")
    
    logger.info(f"Sending prompt to LLM (intro): {intro_text[:200]}...")

    response = await generate_text(final_contents, system_instruction)
    
    logger.info(f"Raw LLM response: {response}")

    # Очистка HTML
    clean_response = clean_html(response)
    if clean_response != response:
        logger.info("Response cleaned from HTML tags.")

    chat_info = await client.get_chat(chat_id)
    chat_title = chat_info.title or chat_info.first_name or "Unknown Chat"
    
    header = f"📊 **Анализ чата:** {chat_title}\n*(Последние {msg_count} сообщений)*\n\n"
    full_text = header + clean_response
    
    logger.info(f"Sending explanation to Saved Messages")
    
    try:
        chunks = split_text(full_text)
        for i, chunk in enumerate(chunks):
            # Если частей несколько, добавляем пометку
            text_to_send = chunk
            if len(chunks) > 1 and i > 0:
                text_to_send = f"...(часть {i+1})\n{chunk}"

            await client.send_message("me", text_to_send, parse_mode=enums.ParseMode.MARKDOWN)
            await asyncio.sleep(0.5)
        
        await asyncio.sleep(DRAFT_COOLDOWN)
        await save_draft(client, chat_id, "✅ Анализ отправлен в Избранное")
        await asyncio.sleep(3.0)
        await save_draft(client, chat_id, "")
        
    except Exception as e:
        logger.error(f"Failed to send: {e}")
        await save_draft(client, chat_id, f"❌ Ошибка отправки")

def register(registry):
    registry.register(['.e', '.explain'], handle_explain_command, "Психопортрет и советы")
