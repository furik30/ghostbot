import asyncio
from utils.gemini_api import generate_text
from utils.common import get_multimodal_history, save_draft
from utils.logger import setup_logger
from pyrogram import Client, enums
from config import DRAFT_COOLDOWN

logger = setup_logger("FunTools")

async def handle_roast_command(client: Client, chat_id: int, args: list):
    """
    Команда .roast — прожарка чата.
    """
    logger.info(f"Roasting chat {chat_id}")

    # 1. Индикация
    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, "🔥 Разогреваю гриль...")

    # 2. История
    history_parts = await get_multimodal_history(client, chat_id, limit=15)

    system_instruction = (
        "Ты — стендап-комик с очень черным и едким чувством юмора. "
        "Твоя задача — жестко, но смешно 'прожарить' (roast) участников чата на основе их сообщений. "
        "Высмеивай их логику, грамотность, стиль общения, темы. "
        "Не сдерживайся. Используй сарказм, иронию и панчи. "
        "Язык: Русский. "
        "Формат: Текст для Telegram (можно использовать Markdown, смайлики)."
    )

    final_contents = ["Here is the chat history to roast:", *history_parts]

    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, "🌶️ Перчу факты...")

    response = await generate_text(final_contents, system_instruction)

    # Отправка
    await save_draft(client, chat_id, "🔥 Прожарка готова!")
    await asyncio.sleep(0.5)

    # Отправляем результат в Saved Messages
    try:
        header = "🔥🔥🔥 **ROAST BATTLE** 🔥🔥🔥\n\n"
        await client.send_message("me", header + response, parse_mode=enums.ParseMode.MARKDOWN)
        await save_draft(client, chat_id, "") # Чистим драфт
    except Exception as e:
        logger.error(f"Failed to send roast: {e}")
        await save_draft(client, chat_id, "❌ Ошибка прожарки")
