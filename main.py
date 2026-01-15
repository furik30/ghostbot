import json
import os
from pyrogram import Client, raw, filters
from config import API_ID, API_HASH, SESSION_NAME, CONTEXT_FILE
from modules import reply_generator, prompt_builder, text_fixer, memo, explain, mimicry, funtools, transcriber, registry
from utils.logger import setup_logger
from utils.common import save_draft

logger = setup_logger("GhostBotCore")

# Инициализация реестра команд
# Импортированные модули:
modules_list = [
    reply_generator, prompt_builder, text_fixer,
    memo, explain, mimicry, funtools, transcriber
]

for mod in modules_list:
    if hasattr(mod, 'register'):
        mod.register(registry.registry)
    else:
        logger.warning(f"Module {mod.__name__} has no register function.")

# Загрузка контекста
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

# 1. ОБРАБОТЧИК ИСХОДЯЩИХ СООБЩЕНИЙ (Перехват отправки)
@app.on_message(filters.me & filters.text)
async def outgoing_message_handler(client: Client, message):
    text = message.text
    if not text:
        return

    # Проверяем, является ли сообщение командой
    handler, trigger, args_text = registry.registry.get_handler(text)

    if handler:
        logger.info(f"Interceptor caught command '{trigger}' in chat {message.chat.id}. Deleting...")
        try:
            # 1. Удаляем отправленное сообщение
            await message.delete()
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")

        # 2. Выполняем команду
        # Аргументы: client, chat_id, text (аргументы), kwargs
        chat_id = message.chat.id
        context_note = chat_contexts.get(str(chat_id), "")

        try:
            await handler(
                client=client,
                chat_id=chat_id,
                text=args_text,
                context_note=context_note,
                chat_contexts=chat_contexts
            )
        except Exception as e:
            logger.error(f"Error executing handler for {trigger}: {e}", exc_info=True)

# 2. ОБРАБОТЧИК ЧЕРНОВИКОВ (Drafts) — "Призрачный режим"
# Позволяет выполнять команды, набрав их в поле ввода, но НЕ отправляя.
# Бот видит черновик, выполняет команду и очищает поле.
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

        # Ищем обработчик через реестр
        handler, trigger, args_text = registry.registry.get_handler(draft_text)
        
        if handler:
            logger.info(f"Draft watcher caught command '{trigger}' in chat {chat_id}")

            # Сразу очищаем черновик, чтобы предотвратить случайную отправку
            # и показать пользователю, что команда принята
            await save_draft(client, chat_id, "")

            context_note = chat_contexts.get(str(chat_id), "")

            try:
                # Выполняем
                await handler(
                    client=client,
                    chat_id=chat_id,
                    text=args_text,
                    context_note=context_note,
                    chat_contexts=chat_contexts
                )
            except Exception as e:
                logger.error(f"Error executing handler for {trigger} via draft: {e}", exc_info=True)
                # В случае ошибки можно вернуть текст в драфт или сообщить логом
                # await save_draft(client, chat_id, f"{draft_text} (Error)")

    except Exception as e:
        logger.error(f"Critical error in draft_watcher: {e}", exc_info=True)

if __name__ == "__main__":
    print("\n------------------------------------")
    print("   👻 GHOST BOT STARTED 👻    ")
    print("------------------------------------\n")
    app.run()
