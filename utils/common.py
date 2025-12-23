from pyrogram import Client, raw
from utils.logger import setup_logger

logger = setup_logger("Utils")

async def save_draft(client: Client, chat_id: int, text: str):
    try:
        logger.info(f"Setting draft in {chat_id}: '{text[:20]}...'")
        peer = await client.resolve_peer(chat_id)
        await client.invoke(raw.functions.messages.SaveDraft(
            peer=peer,
            message=text,
            no_webpage=True
        ))
    except Exception as e:
        logger.error(f"Failed to save draft in {chat_id}: {e}")

async def get_recent_history(client: Client, chat_id: int, limit: int = 10) -> str:
    """Legacy text-only fetcher (для совместимости)"""
    data = await get_multimodal_history(client, chat_id, limit, text_only=True)
    # Возвращаем только текстовую часть первого (и единственного) элемента, если он есть
    if data and isinstance(data[0], str):
        return data[0] 
    return ""

async def get_multimodal_history(client: Client, chat_id: int, limit: int = 10, text_only: bool = False):
    """
    Собирает историю И скачивает медиа (фото, голос, кружочки).
    Возвращает список parts для Gemini.
    """
    parts = []
    logger.info(f"Fetching multimodal history from {chat_id} (limit={limit})...")
    
    messages = []
    async for msg in client.get_chat_history(chat_id, limit=limit):
        messages.append(msg)
    messages.reverse()

    for i, msg in enumerate(messages):
        # 1. Автор
        sender_name = "Unknown"
        if msg.from_user:
            sender_name = "Me (User)" if msg.from_user.is_self else f"{msg.from_user.first_name} {msg.from_user.last_name or ''}".strip()
        elif msg.sender_chat:
            sender_name = msg.sender_chat.title or "Channel"

        logger.info(f"Processing msg {i+1}/{len(messages)} from {sender_name} (ID: {msg.id})")

        # 2. Текст
        text_part = ""
        if msg.text:
            text_part = msg.text
        elif msg.caption:
            text_part = f"[Caption]: {msg.caption}"
        
        msg_header = f"\n--- Msg from {sender_name} ---\n{text_part}"
        parts.append(msg_header)

        if text_only:
            continue

        # 3. Медиа
        try:
            media_bytes = None
            mime_type = ""
            label = ""
            file_size = 0

            # ФОТО
            if msg.photo:
                label = "[Фото]"
                file_size = msg.photo.file_size
                media_stream = await client.download_media(msg, in_memory=True)
                media_bytes = bytes(media_stream.getbuffer())
                mime_type = "image/jpeg"

            # ГОЛОСОВОЕ
            elif msg.voice:
                label = "[Голосовое сообщение]"
                file_size = msg.voice.file_size
                media_stream = await client.download_media(msg, in_memory=True)
                media_bytes = bytes(media_stream.getbuffer())
                mime_type = "audio/ogg"

            # КРУЖОЧЕК (Video Note)
            elif msg.video_note:
                label = "[Видеосообщение / Кружочек]"
                file_size = msg.video_note.file_size
                # Лимит размера 20 MB
                if file_size > 20 * 1024 * 1024:
                    parts.append(f"{label} (Too large to download: {file_size/1024/1024:.2f}MB)")
                    logger.info(f"Video note too large: {file_size}")
                    continue
                    
                media_stream = await client.download_media(msg, in_memory=True)
                media_bytes = bytes(media_stream.getbuffer())
                mime_type = "video/mp4"

            # ОБЫЧНОЕ ВИДЕО (Video)
            elif msg.video:
                label = "[Видео файл]"
                file_size = msg.video.file_size
                # Видео пропускаем намеренно, чтобы не забивать контекст, но добавляем метку
                logger.info(f"Skipping video file (size: {file_size}). Adding placeholder.")
                parts.append(f"{label} (Пропущено для экономии контекста)")
                continue

            # Если скачали - добавляем
            if media_bytes:
                logger.info(f"Downloaded {label} from {sender_name} ({len(media_bytes)} bytes, Type: {mime_type})")
                parts.append(label)
                parts.append({
                    "mime_type": mime_type,
                    "data": media_bytes
                })
            else:
                # Если медиа не скачалось, но сообщение не текстовое и не обработанное выше
                if not text_part:
                    if msg.sticker: parts.append(f"[Стикер: {msg.sticker.emoji}]")
                    elif msg.animation: parts.append("[GIF/Анимация]")
                    elif msg.document: parts.append(f"[Файл: {msg.document.file_name}]")
                    elif msg.video_note: parts.append(f"[Видеосообщение (Ошибка загрузки)]") # Фолбек для кружочка
                    else:
                        # Если совсем пусто (например удаленное сообщение или странный тип)
                         logger.info(f"Message {msg.id} has no text and no supported media.")

        except Exception as e:
            logger.error(f"Failed to download media for msg {msg.id}: {e}")
            parts.append(f"[Ошибка загрузки медиа: {e}]")
            # Для кружочков добавляем явный маркер даже при ошибке
            if msg.video_note:
                 parts.append("[Видеосообщение]")

    logger.info(f"History construction complete. Total parts: {len(parts)}")
    return parts
