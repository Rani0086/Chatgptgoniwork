from pyrogram import Client, filters
from pyrogram.types import Message
from GONI import GONI as app
from GONI import GONI, mongo, LOGGER, db
from GONI.modules.helpers import chatai, CHATBOT_ON, languages

lang_db = db.ChatLangDb.LangCollection
message_cache = {}

async def get_chat_language(chat_id):
    chat_lang = await lang_db.find_one({"chat_id": chat_id})
    return chat_lang["language"] if chat_lang and "language" in chat_lang else None
    
@app.on_message(filters.text, group=2)
async def store_messages(client, message: Message):
    global message_cache

    chat_id = message.chat.id
    chat_lang = await get_chat_language(chat_id)

    if not chat_lang:
        
        if message.from_user and message.from_user.is_bot:
            return

    # Initialize cache for the chat if not already present
        if chat_id not in message_cache:
            message_cache[chat_id] = []

    # Add the new message to the cache
        message_cache[chat_id].append(message)

    # Check if cache has reached 10 messages
        if len(message_cache[chat_id]) >= 10:
        # Create a reply with the last 10 messages
            history = "\n\n".join(
                [
                    f"Text: {msg.text}..."  # Truncated for safety
                    for msg in message_cache[chat_id]
                ]
            )
        
            try:
              # Send the history
                await message.reply(f"Last 10 messages in this chat:\n\n{history}")
            except Exception as e:
                print(f"Failed to send reply: {e}")

        # Clear the cache for this chat
            message_cache[chat_id].clear()
