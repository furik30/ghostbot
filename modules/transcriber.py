import asyncio
from utils.gemini_api import generate_text
from utils.common import save_draft, get_user_firstname
from utils.logger import setup_logger
from utils.text_tools import split_text
from pyrogram import Client, enums
from config import PROMPTS, DRAFT_COOLDOWN

logger = setup_logger("Transcriber")

async def handle_vtt_command(client: Client, chat_id: int, text: str, **kwargs):
    """
    Команда .vtt (.гс) — транскрибация голосовых/видео сообщений.
    Использование: .vtt [кол-во]
    Пример: .vtt 3 (найдет 3 последних голосовых, как глубоко бы они ни были)
    """
    force = kwargs.get('force', False)
    reply_to_id = kwargs.get('reply_to_message_id')

    limit = 20 # Максимальная глубина поиска
    max_msgs_to_process = 5 # По дефолту сколько последних ГС обрабатывать
    args = text.split()
    if args and args[0].isdigit():
        max_msgs_to_process = int(args[0])

    logger.info(f"Looking for {max_msgs_to_process} media msgs in {chat_id} (scan depth={limit})")

    # 1. Индикация
    initial_status = f"🚀 Слушаю {max_msgs_to_process} гс (Force)..." if force else f"👂 Слушаю {max_msgs_to_process} гс..."
    await asyncio.sleep(DRAFT_COOLDOWN)
    await save_draft(client, chat_id, initial_status)

    # 2. Поиск сообщений с аудио
    msgs_to_process = []

    # Мы запрашиваем историю порциями (или до лимита), но фильтруем сами
    async for msg in client.get_chat_history(chat_id, limit=limit):
        # Если мы уже нашли нужное количество — стоп
        if len(msgs_to_process) >= max_msgs_to_process:
            break

        is_media = False
        
        # Проверка на наличие голосового или видео-кружочка
        if msg.voice:
            is_media = True
        elif msg.video_note:
            is_media = True

        if is_media:
            msgs_to_process.append(msg)

    if not msgs_to_process:
        await save_draft(client, chat_id, "❌ Голосовых не найдено")
        await asyncio.sleep(2.0)
        await save_draft(client, chat_id, "")
        return

    # Обрабатываем в хронологическом порядке (от старых к новым)
    msgs_to_process.reverse()

    # 3. Формирование запроса
    user_firstname = await get_user_firstname(client)
    vtt_config = PROMPTS.get('vtt', {})
    raw_instruction = vtt_config.get('system_instruction', "Transcribe audio.")
    common_formatting = PROMPTS.get('common_formatting', "")

    system_instruction = raw_instruction.replace("{common_formatting}", common_formatting)

    processed_count = 0
    full_transcript = "**📝 Расшифровка голосовых:**\n\n"

    status = f"🚀 Расшифровываю ({len(msgs_to_process)} шт)..." if force else f"✍️ Расшифровываю ({len(msgs_to_process)} шт)..."
    await save_draft(client, chat_id, status)

    for msg in msgs_to_process:
        try:
            # Скачиваем медиа
            media_bytes = await client.download_media(msg, in_memory=True)
            media_bytes = bytes(media_bytes.getbuffer())

            mime_type = "audio/ogg" if msg.voice else "video/mp4"
            sender_name = msg.from_user.first_name if msg.from_user else "Unknown"

            # Подготовка контекста для конкретного сообщения
            contents = [
                f"Audio/Video message from {sender_name}:",
                {"mime_type": mime_type, "data": media_bytes}
            ]

            # Генерация текста
            text = await generate_text(contents, system_instruction)

            full_transcript += f"**{sender_name}:** {text}\n\n"
            processed_count += 1

        except Exception as e:
            logger.error(f"Failed to transcribe msg {msg.id}: {e}")
            full_transcript += f"**{sender_name}:** [Ошибка: {e}]\n\n"

    if force:
        signature = "\n\n🤖 *Расшифровка нейросети*"
        full_transcript += signature

    # Отправка
    await save_draft(client, chat_id, "✅ Готово!")
    await asyncio.sleep(0.5)

    try:
        chunks = split_text(full_transcript)
        for i, chunk in enumerate(chunks):
            text_to_send = chunk
            if len(chunks) > 1 and i > 0:
                text_to_send = f"...(часть {i+1})\n{chunk}"

            if force:
                current_reply_to = reply_to_id if i == 0 else None
                await client.send_message(chat_id, text_to_send, parse_mode=enums.ParseMode.MARKDOWN, reply_to_message_id=current_reply_to)
            else:
                await client.send_message("me", text_to_send, parse_mode=enums.ParseMode.MARKDOWN)

            if len(chunks) > 1:
                await asyncio.sleep(0.5)

        if force:
            await asyncio.sleep(3.0)

        await save_draft(client, chat_id, "")
    except Exception as e:
        logger.error(f"Failed to send transcript: {e}")
        await save_draft(client, chat_id, "❌ Ошибка отправки")
        if force:
            await asyncio.sleep(3.0)
            await save_draft(client, chat_id, "")

async def handle_vtt_force(client: Client, chat_id: int, text: str, **kwargs):
    """Обертка для .vttf (Force VTT)"""
    kwargs['force'] = True
    await handle_vtt_command(client, chat_id, text, **kwargs)

def register(registry):
    registry.register(['.vtt', '.гс'], handle_vtt_command, "Расшифровка голосовых")
    registry.register(['.vttf', '.гсf'], handle_vtt_force, "Расшифровка голосовых (сразу в чат)")
