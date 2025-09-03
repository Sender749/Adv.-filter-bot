import asyncio
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from info import ADMINS, LOG_CHANNEL, CHANNELS
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import temp, get_readable_time
import time

lock = asyncio.Lock()

@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    _, ident, chat, lst_msg_id, skip = query.data.split("#")
    if ident == 'yes':
        msg = query.message
        await msg.edit("<b>ɪɴᴅᴇxɪɴɢ sᴛᴀʀᴛᴇᴅ...</b>")
        try:
            chat = int(chat)
        except:
            chat = chat
        await index_files_to_db(int(lst_msg_id), chat, msg, bot, int(skip))
    elif ident == 'cancel':
        temp.CANCEL = True
        await query.message.edit("ᴛʀʏɪɴɢ ᴛᴏ ᴄᴀɴᴄᴇʟ ɪɴᴅᴇxɪɴɢ...")

@Client.on_message(filters.command('index') & filters.private & filters.incoming & filters.user(ADMINS))
async def send_for_index(bot, message):
    if lock.locked():
        return await message.reply('ᴡᴀɪᴛ ᴜɴᴛɪʟ ᴘʀᴇᴠɪᴏᴜs ᴘʀᴏᴄᴇss ᴄᴏᴍᴘʟᴇᴛᴇ.')
    i = await message.reply("ꜰᴏʀᴡᴀʀᴅ ʟᴀsᴛ ᴍᴇssᴀɢᴇ ᴏʀ sᴇɴᴅ ʟᴀsᴛ ᴍᴇssᴀɢᴇ ʟɪɴᴋ.")
    msg = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id)
    await i.delete()
    if msg.text and msg.text.startswith("https://t.me"):
        try:
            msg_link = msg.text.split("/")
            last_msg_id = int(msg_link[-1])
            chat_id = msg_link[-2]
            if chat_id.isnumeric():
                chat_id = int(("-100" + chat_id))
        except:
            await message.reply('ɪɴᴠᴀʟɪᴅ ᴍᴇssᴀɢᴇ ʟɪɴᴋ!')
            return
    elif msg.forward_from_chat and msg.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = msg.forward_from_message_id
        chat_id = msg.forward_from_chat.username or msg.forward_from_chat.id
    else:
        await message.reply('ᴛʜɪs ɪs ɴᴏᴛ ꜰᴏʀᴡᴀʀᴅᴇᴅ ᴍᴇssᴀɢᴇ ᴏʀ ʟɪɴᴋ.')
        return
    try:
        chat = await bot.get_chat(chat_id)
    except Exception as e:
        return await message.reply(f'Errors - {e}')
    if chat.type != enums.ChatType.CHANNEL:
        return await message.reply("ɪ ᴄᴀɴ ɪɴᴅᴇx ᴏɴʟʏ ᴄʜᴀɴɴᴇʟs.")
    s = await message.reply("sᴇɴᴅ sᴋɪᴘ ᴍᴇssᴀɢᴇ ɴᴜᴍʙᴇʀ.")
    msg = await bot.listen(chat_id=message.chat.id, user_id=message.from_user.id)
    await s.delete()
    try:
        skip = int(msg.text)
    except:
        return await message.reply("ɴᴜᴍʙᴇʀ ɪs ɪɴᴠᴀʟɪᴅ.")
    buttons = [[
        InlineKeyboardButton('ʏᴇs', callback_data=f'index#yes#{chat_id}#{last_msg_id}#{skip}')
    ],[
        InlineKeyboardButton('ᴄʟᴏsᴇ', callback_data='close_data'),
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply(f'ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ɪɴᴅᴇx {chat.title} ᴄʜᴀɴɴᴇʟ?\nᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs: <code>{last_msg_id}</code>', reply_markup=reply_markup)

@Client.on_message(filters.command('channel'))
async def channel_info(bot, message):
    if message.from_user.id not in ADMINS:
        await message.reply('ᴏɴʟʏ ᴛʜᴇ ʙᴏᴛ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ... 😑')
        return
    ids = CHANNELS
    if not ids:
        return await message.reply("ɴᴏᴛ sᴇᴛ ᴄʜᴀɴɴᴇʟs")
    text = '**ɪɴᴅᴇxᴇᴅ ᴄʜᴀɴɴᴇʟs:**\n\n'
    for id in ids:
        chat = await bot.get_chat(id)
        text += f'{chat.title}\n'
    text += f'\n**ᴛᴏᴛᴀʟ:** {len(ids)}'
    await message.reply(text)

async def index_files_to_db(lst_msg_id, chat, msg, bot, skip):
    start_time = time.time()
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    current = skip
    
    async with lock:
        try:
            async for message in bot.iter_messages(chat, lst_msg_id, skip):
                time_taken = get_readable_time(time.time()-start_time)
                if temp.CANCEL:
                    temp.CANCEL = False
                    await msg.edit(f"sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴄᴀɴᴄᴇʟʟᴇᴅ!\nᴄᴏᴍᴘʟᴇᴛᴇᴅ ɪɴ {time_taken}\n\nsᴀᴠᴇᴅ <code>{total_files}</code> ꜰɪʟᴇs ᴛᴏ ᴅᴀᴛᴀʙᴀsᴇ!\nᴅᴜᴘʟɪᴄᴀᴛᴇ ꜰɪʟᴇs sᴋɪᴘᴘᴇᴅ: <code>{duplicate}</code>\nᴅᴇʟᴇᴛᴇᴅ ᴍᴇssᴀɢᴇs sᴋɪᴘᴘᴇᴅ: <code>{deleted}</code>\nɴᴏɴ-ᴍᴇᴅɪᴀ ᴍᴇssᴀɢᴇs sᴋɪᴘᴘᴇᴅ: <code>{no_media + unsupported}</code>\nᴜɴsᴜᴘᴘᴏʀᴛᴇᴅ ᴍᴇᴅɪᴀ: <code>{unsupported}</code>\nᴇʀʀᴏʀs ᴏᴄᴄᴜʀʀᴇᴅ: <code>{errors}</code>")
                    return
                current += 1
                if current % 100 == 0:
                    btn = [[
                        InlineKeyboardButton('CANCEL', callback_data=f'index#cancel#{chat}#{lst_msg_id}#{skip}')
                    ]]
                    await msg.edit_text(text=f"ᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs ʀᴇᴄᴇɪᴠᴇᴅ: <code>{current}</code>\nᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs sᴀᴠᴇᴅ: <code>{total_files}</code>\nᴅᴜᴘʟɪᴄᴀᴛᴇ ꜰɪʟᴇs sᴋɪᴘᴘᴇᴅ: <code>{duplicate}</code>\nᴅᴇʟᴇᴛᴇᴅ ᴍᴇssᴀɢᴇs sᴋɪᴘᴘᴇᴅ: <code>{deleted}</code>\nɴᴏɴ-ᴍᴇᴅɪᴀ ᴍᴇssᴀɢᴇs sᴋɪᴘᴘᴇᴅ: <code>{no_media + unsupported}</code>\nᴜɴsᴜᴘᴘᴏʀᴛᴇᴅ ᴍᴇᴅɪᴀ: <code>{unsupported}</code>\nᴇʀʀᴏʀs ᴏᴄᴄᴜʀʀᴇᴅ: <code>{errors}</code>", reply_markup=InlineKeyboardMarkup(btn))
                    await asyncio.sleep(2)
                if message.empty:
                    deleted += 1
                    continue
                elif not message.media:
                    no_media += 1
                    continue
                elif message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.DOCUMENT]:
                    unsupported += 1
                    continue
                media = getattr(message, message.media.value, None)
                if not media:
                    unsupported += 1
                    continue
                elif media.mime_type not in ['video/mp4', 'video/x-matroska']:
                    unsupported += 1
                    continue
                media.caption = message.caption
                sts = await save_file(media)
                if sts == 'suc':
                    total_files += 1
                elif sts == 'dup':
                    duplicate += 1
                elif sts == 'err':
                    errors += 1
        except FloodWait as e:
            await asyncio.sleep(e.x)
        except Exception as e:
            await msg.reply(f'ɪɴᴅᴇx ᴄᴀɴᴄᴇʟᴇᴅ ᴅᴜᴇ ᴛᴏ ᴇʀʀᴏʀ - {e}')
        else:
            time_taken = get_readable_time(time.time()-start_time)
            await msg.edit(f'sᴜᴄᴄᴇsꜰᴜʟʟʏ sᴀᴠᴇᴅ <code>{total_files}</code> ᴛᴏ ᴅᴀᴛᴀʙᴀsᴇ!\nᴄᴏᴍᴘʟᴇᴛᴇᴅ ɪɴ {time_taken}\n\nᴅᴜᴘʟɪᴄᴀᴛᴇ ꜰɪʟᴇs sᴋɪᴘᴘᴇᴅ: <code>{duplicate}</code>\nᴅᴇʟᴇᴛᴇᴅ ᴍᴇssᴀɢᴇs sᴋɪᴘᴘᴇᴅ: <code>{deleted}</code>\nɴᴏɴ-ᴍᴇᴅɪᴀ ᴍᴇssᴀɢᴇs sᴋɪᴘᴘᴇᴅ: <code>{no_media + unsupported}</code>\nᴜɴsᴜᴘᴘᴏʀᴛᴇᴅ ᴍᴇᴅɪᴀ: <code>{unsupported}</code>\nᴇʀʀᴏʀs ᴏᴄᴄᴜʀʀᴇᴅ: <code>{errors}</code>')
