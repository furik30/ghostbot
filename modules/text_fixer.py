import asyncio
from utils.gemini_api import generate_text
from utils.common import save_draft, get_user_firstname
from utils.logger import setup_logger
from pyrogram import Client
from config import PROMPTS, DRAFT_COOLDOWN

logger = setup_logger("TextFixer")

async def handle_fix_command(client: Client, chat_id: int, text: str, **kwargs):
    """
    Обработчик .fix
    Поддерживает:
    1. Префикс: .fix Текст (text = "Текст")
    2. Инфикс/Постфикс: Текст .fix Инструкция (text = "Текст .fix Инструкция") - благодаря registry, возвращающему полный текст
    """
    
    # Попытка найти разделитель " .fix" (с пробелом перед точкой)
    if " .fix" in text:
        parts = text.split(" .fix", 1)
        original_text = parts[0].strip()
        user_instruction = parts[1].strip() if len(parts) > 1 else ""
    elif text.startswith(".fix "):
        # Если пришло как префикс, но registry уже обрезал ".fix " в начале,
        # то 'text' это уже чистый контент.
        # Но если registry вернул полный текст (в случае не-префиксного поиска), то обрабатываем выше.
        # А если registry отрезал префикс, то text не содержит ".fix" в начале.
        original_text = text.strip()
        user_instruction = ""
    else:
        # Fallback: просто текст
        original_text = text.strip()
        user_instruction = ""

    logger.info(f"Fixing text length: {len(original_text)}. Instruction: {user_instruction}")

    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, "🔧 Полирую текст...")

    user_firstname = await get_user_firstname(client)
    fixer_config = PROMPTS.get('text_fixer', {})
    raw_instruction = fixer_config.get('system_instruction', "Fix the text.")

    system_instruction = raw_instruction.replace("{user_firstname}", user_firstname)

    contents = [
        f"Constraint: Do not significantly increase the text length.",
        f"USER INSTRUCTION: {user_instruction}",
        f"---\nInput text: {original_text}"
    ]

    response = await generate_text(contents, system_instruction)

    if len(response) > 4000:
        logger.warning("Response too long, sending to Saved Messages.")
        try:
            await client.send_message("me", f"🔧 **Fixed Text:**\n\n{response}")
            await asyncio.sleep(DRAFT_COOLDOWN)
            await save_draft(client, chat_id, "📦 Результат в Избранном (слишком длинный).")
            await asyncio.sleep(3.0)
            await save_draft(client, chat_id, "") 
        except Exception as e:
            logger.error(f"Failed to send to Saved Messages: {e}")
            await save_draft(client, chat_id, "❌ Ошибка размера.")
    else:
        await asyncio.sleep(DRAFT_COOLDOWN)
        await save_draft(client, chat_id, response)

def register(registry):
    registry.register(['.fix'], handle_fix_command, "Исправление текста")
