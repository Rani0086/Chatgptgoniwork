import logging
import os
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid
import config
from GONI.mplugin.helpers import is_owner
from config import API_HASH, API_ID, OWNER_ID
from GONI import CLONE_OWNERS
from GONI import GONI as app
from GONI import db as mongodb

CLONES = set()
cloneownerdb = mongodb.cloneownerdb
clonebotdb = mongodb.clonebotdb

async def save_clonebot_owner(bot_id, user_id):
    await cloneownerdb.insert_one({"bot_id": bot_id, "user_id": user_id})

@Client.on_message(filters.command(["clone", "host", "deploy"]))
async def clone_txt(client, message):
    if len(message.command) > 1:
        bot_token = message.text.split("/clone", 1)[1].strip()
        mi = await message.reply_text("Please wait while I check the bot token.")
        try:
            ai = Client(bot_token, API_ID, API_HASH, bot_token=bot_token, plugins=dict(root="GONI/mplugin"))
            await ai.start()
            bot = await ai.get_me()
            bot_id = bot.id
            user_id = message.from_user.id
            CLONE_OWNERS[bot_id] = user_id
            await ai.set_bot_commands([
                    BotCommand("start", "Start the bot"),
                    BotCommand("help", "Get the help menu"),
                    BotCommand("clone", "Make your own chatbot"),
                    BotCommand("ping", "Check if the bot is alive or dead"),
                    BotCommand("lang", "Select bot reply language"),
                    BotCommand("resetlang", "Reset to default bot reply lang"),
                    BotCommand("id", "Get users user_id"),
                    BotCommand("stats", "Check bot stats"),
                    BotCommand("gcast", "Broadcast any message to groups/users"),
                    BotCommand("chatbot", "Enable or disable chatbot"),
                    BotCommand("status", "Check chatbot enable or disable in chat"),
                    BotCommand("shayri", "Get random shayri for love"),
                    BotCommand("repo", "Get chatbot source code"),
                ])
        except (AccessTokenExpired, AccessTokenInvalid):
            await mi.edit_text("**Invalid bot token. Please provide a valid one.**")
            return
        except Exception as e:
            cloned_bot = await clonebotdb.find_one({"token": bot_token})
            if cloned_bot:
                await mi.edit_text("**🤖 Your bot is already cloned ✅**")
                return

        await mi.edit_text("**Cloning process started. Please wait for the bot to start.**")
        try:
            details = {
                "bot_id": bot.id,
                "is_bot": True,
                "user_id": user_id,
                "name": bot.first_name,
                "token": bot_token,
                "username": bot.username,
            }

            await app.send_message(
                int(OWNER_ID), f"**#New_Clone**\n\n**Bot:- @{bot.username}**\n\n**Details:-**\n{details}"
            )

            await clonebotdb.insert_one(details)
            await save_clonebot_owner(bot.id, user_id)
            CLONES.add(bot.id)

            await mi.edit_text(
                f"**Bot @{bot.username} has been successfully cloned and started ✅.**\n**Remove clone by :- /delclone**\n**Check all cloned bot list by:- /cloned**"
            )
        except BaseException as e:
            logging.exception("Error while cloning bot.")
            await mi.edit_text(
                f"⚠️ <b>Error:</b>\n\n<code>{e}</code>\n\n**Forward this message to @THE_VIP_BOY_OP for assistance**"
            )
    else:
        await message.reply_text("**Provide Bot Token after /clone Command from @Botfather.**")


@Client.on_message(filters.command("cloned"))
async def list_cloned_bots(client, message):
    try:
        cloned_bots = clonebotdb.find()
        cloned_bots_list = await cloned_bots.to_list(length=None)
        if not cloned_bots_list:
            await message.reply_text("No bots have been cloned yet.")
            return
        total_clones = len(cloned_bots_list)
        text = f"**Total Cloned Bots:** {total_clones}\n\n"
        for bot in cloned_bots_list:
            text += f"**Bot ID:** `{bot['bot_id']}`\n"
            text += f"**Bot Name:** {bot['name']}\n"
            text += f"**Bot Username:** @{bot['username']}\n\n"
        await message.reply_text(text)
    except Exception as e:
        logging.exception(e)
        await message.reply_text("**An error occurred while listing cloned bots.**")

@Client.on_message(
    filters.command(["deletecloned", "delcloned", "delclone", "deleteclone", "removeclone", "cancelclone"])
)
async def delete_cloned_bot(client, message):
    try:
        if len(message.command) < 2:
            await message.reply_text("**⚠️ Please provide the bot token after the command.**")
            return

        bot_token = " ".join(message.command[1:])
        ok = await message.reply_text("**Checking the bot token...**")

        cloned_bot = await clonebotdb.find_one({"token": bot_token})
        if cloned_bot:
            await clonebotdb.delete_one({"token": bot_token})
            CLONES.remove(cloned_bot["bot_id"])
            await ok.edit_text(
                "**🤖 your cloned bot has been disconnected from my server ☠️**\n**Clone by :- /clone**"
            )
            os.system(f"kill -9 {os.getpid()} && bash start")
        else:
            await message.reply_text("**⚠️ The provided bot token is not in the cloned list.**")
    except Exception as e:
        await message.reply_text(f"**An error occurred while deleting the cloned bot:** {e}")
        logging.exception(e)


@Client.on_message(filters.command("delallclone") & filters.user(int(OWNER_ID)))
async def delete_all_cloned_bots(client, message):
    try:
        a = await message.reply_text("**Deleting all cloned bots...**")
        await clonebotdb.delete_many({})
        CLONES.clear()
        await a.edit_text("**All cloned bots have been deleted successfully ✅**")
    except Exception as e:
        await a.edit_text(f"**An error occurred while deleting all cloned bots.** {e}")
        logging.exception(e)