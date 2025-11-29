import logging
import json
import os
from pyrogram import Client, raw
from config import API_ID, API_HASH, SESSION_NAME, CONTEXT_FILE
from modules import reply_generator, prompt_builder, text_fixer, memo, explain, mimicry
from utils.logger import setup_logger

logger = setup_logger("GhostBotCore")

if os.path.exists(CONTEXT_FILE):
    with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
        chat_contexts = json.load(f)
    logger.info(f"Loaded {len(chat_contexts)} context notes.")
else:
    chat_contexts = {}
    logger.info("No context file found, starting fresh.")

def save_context(data):
    with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

app = Client(f"sessions/{SESSION_NAME}", api_id=API_ID, api_hash=API_HASH)

@app.on_raw_update()
async def draft_watcher(client: Client, update, users, chats):
    if not isinstance(update, raw.types.UpdateDraftMessage):
        return

    try:
        peer = update.peer
        chat_id = None
        if isinstance(peer, raw.types.PeerUser):
            chat_id = peer.user_id
        elif isinstance(peer, raw.types.PeerChat):
            chat_id = -peer.chat_id
        elif isinstance(peer, raw.types.PeerChannel):
            chat_id = int(f"-100{peer.channel_id}")
        
        if not chat_id:
            return

        if isinstance(update.draft, raw.types.DraftMessageEmpty):
            return

        draft_text = update.draft.message
        if not draft_text:
            return

        if draft_text.startswith(".r ") or draft_text.startswith(".к "):
            logger.info(f"Command .r detected in {chat_id}")
            args = draft_text.split()[1:] 
            context_note = chat_contexts.get(str(chat_id), "")
            await reply_generator.handle_reply_command(client, chat_id, args, context_note)

        elif draft_text.startswith(".p ") or draft_text.startswith(".prompt "):
            logger.info(f"Command .p detected in {chat_id}")
            await prompt_builder.handle_prompt_command(client, chat_id, draft_text)

        elif ".fix" in draft_text:
            if draft_text.endswith(" .fix") or ".fix " in draft_text:
                logger.info(f"Command .fix detected in {chat_id}")
                await text_fixer.handle_fix_command(client, chat_id, draft_text)

        elif draft_text.startswith(".memo "):
            logger.info(f"Command .memo detected in {chat_id}")
            await memo.handle_memo_command(client, chat_id, draft_text, chat_contexts)
        
        elif draft_text.startswith(".memoshow") or draft_text == ".ms":
            logger.info(f"Command .memoshow detected in {chat_id}")
            await memo.handle_memoshow_command(client, chat_id, chat_contexts)
            
        elif draft_text.startswith(".mimi"):
            logger.info(f"Command .mimi detected in {chat_id}")
            await mimicry.handle_mimicry_command(client, chat_id, chat_contexts)
            
        elif draft_text.startswith(".e ") or draft_text.startswith(".explain "):
            logger.info(f"Command .e detected in {chat_id}")
            args = draft_text.split()[1:]
            context_note = chat_contexts.get(str(chat_id), "")
            await explain.handle_explain_command(client, chat_id, args, context_note)

    except Exception as e:
        logger.error(f"Critical error in draft_watcher: {e}", exc_info=True)

if __name__ == "__main__":
    print("\n------------------------------------")
    print("   👻 GHOST BOT STARTED 👻    ")
    print("------------------------------------\n")
    app.run()