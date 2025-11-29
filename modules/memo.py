import json
import os
import asyncio
from config import CONTEXT_FILE
from utils.common import save_draft
from utils.logger import setup_logger
from pyrogram import Client

logger = setup_logger("MemoModule")

async def handle_memo_command(client: Client, chat_id: int, raw_text: str, chat_contexts: dict):
    note = raw_text[6:].strip()
    
    if not note:
        await asyncio.sleep(2)
        await save_draft(client, chat_id, "⚠️ Текст заметки пуст")
        return

    chat_contexts[str(chat_id)] = note
    
    try:
        with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_contexts, f, ensure_ascii=False, indent=2)
        logger.info(f"Updated memo for chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to save context: {e}")
        await asyncio.sleep(2)
        await save_draft(client, chat_id, "❌ Ошибка сохранения")
        return

    await asyncio.sleep(2)
    await save_draft(client, chat_id, "💾 Контекст обновлен!")
    
    await asyncio.sleep(2.0)
    await save_draft(client, chat_id, "") 


async def handle_memoshow_command(client: Client, chat_id: int, chat_contexts: dict):
    current_note = chat_contexts.get(str(chat_id), "")
    
    if not current_note:
        await asyncio.sleep(2)
        await save_draft(client, chat_id, "📂 Заметок нет. Напиши .mimi для авто-создания.")
        
        await asyncio.sleep(3.0)
        await save_draft(client, chat_id, "")
        return
        
    command_to_show = f".memo {current_note}"
    
    await asyncio.sleep(2)
    await save_draft(client, chat_id, command_to_show)