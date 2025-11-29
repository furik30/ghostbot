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

    for msg in messages:
        # 1. Автор
        sender_name = "Unknown"
        if msg.from_user:
            sender_name = "Me (User)" if msg.from_user.is_self else f"{msg.from_user.first_name} {msg.from_user.last_name or ''}".strip()
        elif msg.sender_chat:
            sender_name = msg.sender_chat.title or "Channel"

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

            # ФОТО
            if msg.photo:
                label = "[Photo]"
                media_stream = await client.download_media(msg, in_memory=True)
                media_bytes = bytes(media_stream.getbuffer())
                mime_type = "image/jpeg"

            # ГОЛОСОВОЕ
            elif msg.voice:
                label = "[Voice Message]"
                media_stream = await client.download_media(msg, in_memory=True)
                media_bytes = bytes(media_stream.getbuffer())
                mime_type = "audio/ogg"

            # КРУЖОЧЕК (Video Note) - ДОБАВЛЕНО
            elif msg.video_note:
                label = "[Video Note / Кружочек]"
                # Лимит размера (чтобы не вешать VDS на скачивании 100мб), кружочки обычно легкие
                if msg.video_note.file_size > 20 * 1024 * 1024: # 20 MB limit
                    parts.append("[Video Note too large to download]")
                    continue
                    
                media_stream = await client.download_media(msg, in_memory=True)
                media_bytes = bytes(media_stream.getbuffer())
                mime_type = "video/mp4"

            # ОБЫЧНОЕ ВИДЕО (Video) - ДОБАВЛЕНО
            elif msg.video:
                label = "[Video File]"
                # Видео может быть большим, качаем только маленькие
                if msg.video.file_size > 15 * 1024 * 1024: # 15 MB limit
                    parts.append(f"[Video File: {msg.video.file_name or 'video'} (too large)]")
                    continue
                
                media_stream = await client.download_media(msg, in_memory=True)
                media_bytes = bytes(media_stream.getbuffer())
                mime_type = "video/mp4"

            # Если скачали - добавляем
            if media_bytes:
                logger.info(f"Downloaded {label} from {sender_name} ({len(media_bytes)} bytes)")
                parts.append(label)
                parts.append({
                    "mime_type": mime_type,
                    "data": media_bytes
                })
            elif not text_part:
                if msg.sticker: parts.append(f"[Sticker: {msg.sticker.emoji}]")
                elif msg.animation: parts.append("[GIF/Animation]")
                elif msg.document: parts.append(f"[File: {msg.document.file_name}]")
                else: parts.append("[Unsupported Media]")

        except Exception as e:
            logger.error(f"Failed to download media for msg {msg.id}: {e}")
            parts.append(f"[Error downloading media: {e}]")

    return parts