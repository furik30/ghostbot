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
    """Legacy text-only fetcher (быстрый)"""
    data = await get_multimodal_history(client, chat_id, limit, text_only=True)
    return data[0] if data else ""

async def get_multimodal_history(client: Client, chat_id: int, limit: int = 10, text_only: bool = False):
    """
    Собирает историю И скачивает медиа (фото, голос).
    Возвращает список parts для Gemini.
    """
    parts = []
    
    logger.info(f"Fetching multimodal history from {chat_id} (limit={limit})...")
    
    messages = []
    async for msg in client.get_chat_history(chat_id, limit=limit):
        messages.append(msg)
    messages.reverse()

    for msg in messages:
        sender_name = "Unknown"
        if msg.from_user:
            sender_name = "Me (User)" if msg.from_user.is_self else f"{msg.from_user.first_name} {msg.from_user.last_name or ''}".strip()
        elif msg.sender_chat:
            sender_name = msg.sender_chat.title or "Channel"

        text_part = ""
        if msg.text:
            text_part = msg.text
        elif msg.caption:
            text_part = f"[Caption]: {msg.caption}"
        
        parts.append(f"\n--- Msg from {sender_name} ---\n{text_part}")

        if text_only:
            if msg.photo: parts.append("[Photo]")
            if msg.voice: parts.append("[Voice Message]")
            continue

        try:
            media_bytes = None
            mime_type = ""
            label = ""

            if msg.photo:
                label = "[Photo Content]"
                media_stream = await client.download_media(msg, in_memory=True)
                media_bytes = bytes(media_stream.getbuffer())
                mime_type = "image/jpeg"

            elif msg.voice:
                label = "[Voice Audio]"
                media_stream = await client.download_media(msg, in_memory=True)
                media_bytes = bytes(media_stream.getbuffer())
                mime_type = "audio/ogg"

            if media_bytes:
                logger.info(f"Downloaded {label} from {sender_name} ({len(media_bytes)} bytes)")
                parts.append(label)
                parts.append({
                    "mime_type": mime_type,
                    "data": media_bytes
                })
        except Exception as e:
            logger.error(f"Failed to download media for msg {msg.id}: {e}")
            parts.append(f"[Error downloading media: {e}]")

    return parts