import json
import asyncio
from config import CONTEXT_FILE, DRAFT_COOLDOWN
from utils.common import save_draft
from utils.logger import setup_logger
from pyrogram import Client

logger = setup_logger("MemoModule")

async def handle_memo_command(client: Client, chat_id: int, text: str, **kwargs):
    """
    Обработчик .memo <текст>
    """
    # chat_contexts передается через kwargs
    chat_contexts = kwargs.get("chat_contexts", {})
    note = text.strip()
    
    if not note:
        await asyncio.sleep(DRAFT_COOLDOWN)
        await save_draft(client, chat_id, "⚠️ Текст заметки пуст")
        return

    chat_contexts[str(chat_id)] = note
    
    try:
        with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
            json.dump(chat_contexts, f, ensure_ascii=False, indent=2)
        logger.info(f"Updated memo for chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to save context: {e}")
        await asyncio.sleep(DRAFT_COOLDOWN)
        await save_draft(client, chat_id, "❌ Ошибка сохранения")
        return

    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, "💾 Контекст обновлен!")
    
    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, "") 


async def handle_memoshow_command(client: Client, chat_id: int, text: str, **kwargs):
    chat_contexts = kwargs.get("chat_contexts", {})
    current_note = chat_contexts.get(str(chat_id), "")
    
    if not current_note:
        await asyncio.sleep(DRAFT_COOLDOWN)
        await save_draft(client, chat_id, "📂 Заметок нет. Напиши .mimi для авто-создания.")
        
        await asyncio.sleep(3.0)
        await save_draft(client, chat_id, "")
        return
        
    command_to_show = f".memo {current_note}"
    
    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, command_to_show)

def register(registry):
    registry.register(['.memo'], handle_memo_command, "Сохранить заметку")
    registry.register(['.memoshow', '.ms'], handle_memoshow_command, "Показать заметку")
