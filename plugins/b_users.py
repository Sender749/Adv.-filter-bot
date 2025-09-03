from pyrogram.raw.types import UpdateBotStopped
from pyrogram.types import Update
from database.users_chats_db import db
import logging
from pyrogram import Client, ContinuePropagation, filters
from utils import temp
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message 
from info import USERNAME

@Client.on_raw_update(group=-15)
async def blocked_user(_: Client, u: Update, __: dict, ___: dict):
    if not isinstance(u, UpdateBotStopped):
        raise ContinuePropagation
    if not u.stopped:
        return
    await db.delete_user(u.user_id)
    logging.info(f"{u.user_id} - Removed from Database, since blocked account.")

async def banned_users(_, __, message: Message):
    return (
        message.from_user is not None or not message.sender_chat
    ) and message.from_user.id in temp.BANNED_USERS

banned_user = filters.create(banned_users)

async def disabled_chat(_, __, message: Message):
    return message.chat.id in temp.BANNED_CHATS

disabled_group=filters.create(disabled_chat)

@Client.on_message(filters.private & banned_user & filters.incoming)
async def is_user_banned(bot, message):
    buttons = [[
        InlineKeyboardButton('Support', url=USERNAME)
    ]]
    reply_markup=InlineKeyboardMarkup(buttons)
    ban = await db.get_ban_status(message.from_user.id)  # Added await
    await message.reply(f'Sorry {message.from_user.mention},\nMy owner you are banned to use me! If you want to know more about it contact support group.\nReason - <code>{ban["ban_reason"]}</code>',
                        reply_markup=reply_markup)

@Client.on_message(filters.group & disabled_group & filters.incoming)
async def is_group_disabled(bot, message):
    buttons = [[
        InlineKeyboardButton('Support', url=USERNAME)
    ]]
    reply_markup=InlineKeyboardMarkup(buttons)
    vazha = await db.get_chat(message.chat.id)  # Added await
    k = await message.reply(
        text=f"<b><u>Chat Not Allowed</u></b>\n\nMy owner has restricted me from working here! If you want to know more about it contact support group.\nReason - <code>{vazha['reason']}</code>",
        reply_markup=reply_markup)
    try:
        await k.pin()
    except:
        pass
    await bot.leave_chat(message.chat.id)
