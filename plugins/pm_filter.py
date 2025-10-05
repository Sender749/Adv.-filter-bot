 import asyncio
import re
import math
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from info import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, ChatPermissions, ReplyKeyboardMarkup
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid, ChatAdminRequired
from utils import temp, get_settings, is_check_admin, get_status, get_size, save_group_settings, is_subscribed, is_req_subscribed, get_poster, get_status, get_readable_time , imdb , formate_file_name, process_trending_data, create_keyboard_layout, log_error, group_setting_buttons
from database.users_chats_db import db
from database.extra_db import silicondb
from database.ia_filterdb import collection, is_second_db_configured, second_collection, get_search_results, delete_files
import random
lock = asyncio.Lock()
import traceback
from fuzzywuzzy import process
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
FILES_ID = {}
CAP = {}

@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_search(client, message):
    if message.text.startswith("/"):
        return
    sili = silicondb.get_bot_sttgs()
    if not sili.get('PM_SEARCH', False) if sili else False:
        return await message.reply_text('<b><i>ᴘᴍ sᴇᴀʀᴄʜ ᴡᴀs ᴅɪsᴀʙʟᴇᴅ sᴇᴀʀᴄʜ ɪɴ ᴍᴏᴠɪᴇ ɢʀᴏᴜᴘ!</i></b>')

    if not sili.get('AUTO_FILTER', True) if sili else True:
        return await message.reply_text('<b><i>ᴀᴜᴛᴏ ꜰɪʟᴛᴇʀ ᴡᴀs ᴅɪsᴀʙʟᴇᴅ!</i></b>')

    await auto_filter(client, message)


@Client.on_message(filters.group & filters.text & filters.incoming)
async def group_search(client, message):
    user_id = message.from_user.id if message.from_user else None
    chat_id = message.chat.id
    settings = await get_settings(chat_id)
    sili = silicondb.get_bot_sttgs()

    if message.chat.id == SUPPORT_GROUP :
                if message.text.startswith("/"):
                    return
                files, n_offset, total = await get_search_results(message.text, offset=0)
                if total != 0:
                    link = await db.get_set_grp_links(index=1)
                    msg = await message.reply_text(script.SUPPORT_GRP_MOVIE_TEXT.format(message.from_user.mention() , total) ,             reply_markup=InlineKeyboardMarkup([
                        [ InlineKeyboardButton('ɢᴇᴛ ꜰɪʟᴇs ꜰʀᴏᴍ ʜᴇʀᴇ 😉' , url=link)]
                        ]))
                    await asyncio.sleep(300)
                    return await msg.delete()
                else: return   

    if not sili.get('AUTO_FILTER', True) if sili else True:
        return await message.reply_text('<b><i>ᴀᴜᴛᴏ ꜰɪʟᴛᴇʀ ᴡᴀs ᴅɪsᴀʙʟᴇᴅ!</i></b>')

    if settings["auto_filter"]:
        if not user_id:
            await message.reply("<b>🚨 ɪ'ᴍ ɴᴏᴛ ᴡᴏʀᴋɪɴɢ ꜰᴏʀ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ!</b>")
            return

        if 'hindi' in message.text.lower() or 'tamil' in message.text.lower() or 'telugu' in message.text.lower() or 'malayalam' in message.text.lower() or 'kannada' in message.text.lower() or 'english' in message.text.lower() or 'gujarati' in message.text.lower(): 
            return await auto_filter(client, message)

        elif message.text.startswith("/"):
            return

        elif re.findall(r'https?://\S+|www\.\S+|t\.me/\S+', message.text):
            if await is_check_admin(client, message.chat.id, message.from_user.id):
                return
            await message.delete()
            return await message.reply("<b>sᴇɴᴅɪɴɢ ʟɪɴᴋ ɪsɴ'ᴛ ᴀʟʟᴏᴡᴇᴅ ʜᴇʀᴇ ❌🤞🏻</b>")

        elif '@admin' in message.text.lower() or '@admins' in message.text.lower():
            if await is_check_admin(client, message.chat.id, message.from_user.id):
                return
            admins = []
            async for member in client.get_chat_members(chat_id=message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                if not member.user.is_bot:
                    admins.append(member.user.id)
                    if member.status == enums.ChatMemberStatus.OWNER:
                        if message.reply_to_message:
                            try:
                                sent_msg = await message.reply_to_message.forward(member.user.id)
                                await sent_msg.reply_text(f"#Attention\n★ User: {message.from_user.mention}\n★ Group: {message.chat.title}\n\n★ <a href={message.reply_to_message.link}>Go to message</a>", disable_web_page_preview=True)
                            except:
                                pass
                        else:
                            try:
                                sent_msg = await message.forward(member.user.id)
                                await sent_msg.reply_text(f"#Attention\n★ User: {message.from_user.mention}\n★ Group: {message.chat.title}\n\n★ <a href={message.link}>Go to message</a>", disable_web_page_preview=True)
                            except:
                                pass
            hidden_mentions = (f'[\u2064](tg://user?id={user_id})' for user_id in admins)
            await message.reply_text('<code>Report sent</code>' + ''.join(hidden_mentions))
            return               
        else:
            try: 
                await auto_filter(client, message)
            except Exception as e:
                traceback.print_exc()
                print('found err in grp search  :',e)

    else:
        k=await message.reply_text('<b>⚠️ ᴀᴜᴛᴏ ꜰɪʟᴛᴇʀ ᴍᴏᴅᴇ ɪꜱ ᴏꜰꜰ...</b>')
        await asyncio.sleep(10)
        await k.delete()
        try:
            await message.delete()
        except:
            pass

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    try:
        ident, req, key, offset = query.data.split("_")

        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)

        offset = max(0, int(offset))  
        search = BUTTONS.get(key)
        cap = CAP.get(key, "")

        if not search:
            return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

        files, n_offset, total = await get_search_results(search, offset=offset)
        n_offset = int(n_offset) if n_offset else 0

        if not files:
            return await query.answer("No files found", show_alert=True)

        temp.FILES_ID[key] = files
        temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = files
        temp.CHAT[query.from_user.id] = query.message.chat.id

        settings = await get_settings(query.message.chat.id)
        max_btn = int(MAX_BTN)
        current_page = (offset // max_btn) + 1
        total_pages = math.ceil(total / max_btn)

        del_msg = f"\n\n<b>⚠️ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴀꜰᴛᴇʀ <code>{get_readable_time(DELETE_TIME)}</code> ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs</b>" if settings.get("auto_delete") else ""

        if settings.get("link"):
            links = "".join([
                f"<b>\n\n{i}. <a href=https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{f['_id']}>[{get_size(f['file_size'])}] {' '.join(filter(lambda x: not any(x.startswith(p) for p in ['[', '@', 'www.']), f['file_name'].split()))}</a></b>"
                for i, f in enumerate(files, offset + 1)
            ])
            btn = []
        else:
            links = ""
            btn = [[
                InlineKeyboardButton(
                    f"📁 {get_size(f['file_size'])}≽ {f.get('caption', formate_file_name(f['file_name']))}",
                    url=f"https://telegram.dog/{temp.U_NAME}?start=file_{query.message.chat.id}_{f['_id']}"
                )
            ] for f in files]

        btn.insert(0, [InlineKeyboardButton("• ʟᴀɴɢᴜᴀɢᴇ •", callback_data=f"languages#{key}#{offset}#{req}")])
        btn.insert(1, [
            InlineKeyboardButton("• ǫᴜᴀʟɪᴛʏ •", callback_data=f"qualities#{key}#{offset}#{req}"),
            InlineKeyboardButton("• sᴇᴀsᴏɴ •", callback_data=f"seasons#{key}#{offset}#{req}")
        ])
        btn.insert(2, [InlineKeyboardButton("• sᴇɴᴅ ᴀʟʟ •", callback_data=f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}")])

        nav_row = []
        if offset > 0:
            back_offset = max(0, offset - max_btn)
            nav_row.append(InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{back_offset}"))

        nav_row.append(InlineKeyboardButton(f"{current_page} / {total_pages}", callback_data="pages"))

        if n_offset > 0:
            nav_row.append(InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"next_{req}_{key}_{n_offset}"))

        btn.append(nav_row)

        if settings.get("link"):
            await query.message.edit_text(
                cap + links + del_msg, 
                disable_web_page_preview=True, 
                parse_mode=enums.ParseMode.HTML, 
                reply_markup=InlineKeyboardMarkup(btn)
            )
        else:
            try:
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
            except MessageNotModified:
                pass
            await query.answer()

    except Exception as e:
        await query.answer("Error processing request", show_alert=True)

@Client.on_callback_query(filters.regex(r"^seasons#"))
async def seasons_cb_handler(client: Client, query: CallbackQuery):
    _, key, offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)

    btn = []
    for i in range(0, len(SEASONS), 2):
        text1, cb1 = SEASONS[i]
        row = [InlineKeyboardButton(text1, callback_data=f"season_search#{cb1}#{key}#0#{offset}#{req}")]
        if i + 1 < len(SEASONS):
            text2, cb2 = SEASONS[i + 1]
            row.append(InlineKeyboardButton(text2, callback_data=f"season_search#{cb2}#{key}#0#{offset}#{req}"))
        btn.append(row)

    btn.append([InlineKeyboardButton("⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_0")])

    await query.message.edit_text(
        "<b>ɪɴ ᴡʜɪᴄʜ sᴇᴀsᴏɴ ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ, ᴄʜᴏᴏsᴇ ꜰʀᴏᴍ ʜᴇʀᴇ ↓↓</b>", 
        reply_markup=InlineKeyboardMarkup(btn)
    )

@Client.on_callback_query(filters.regex(r"^season_search#"))
async def season_search(client: Client, query: CallbackQuery):
    _, season, key, offset, original_offset, req = query.data.split("#")

    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)

    search = BUTTONS.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    current_offset = int(offset)
    max_btn = int(MAX_BTN)

    try:
        seas_num = int(season[1:])  # Extract number from "s01" -> 1
        seas = f"S0{seas_num}" if seas_num < 10 else f"S{seas_num}"
        season_patterns = [seas, season]
    except (ValueError, IndexError):
        return await query.answer("Invalid season format", show_alert=True)

    all_files, search_offset = [], 0
    while True:
        batch_files, next_offset, _ = await get_search_results(search.replace("_", " "), max_btn, search_offset)
        if not batch_files:
            break
        all_files.extend(batch_files)
        search_offset = int(next_offset) if next_offset else None
        if not search_offset:
            break

    filtered_files = [f for f in all_files if any(re.search(p, f['file_name'], re.IGNORECASE) for p in season_patterns)]

    if not filtered_files:
        return await query.answer(f"sᴏʀʀʏ {season.title()} ɴᴏᴛ ꜰᴏᴜɴᴅ ꜰᴏʀ {search.replace('_', ' ')}", show_alert=True)

    page_files = filtered_files[current_offset:current_offset + max_btn]
    total_filtered = len(filtered_files)
    current_page = (current_offset // max_btn) + 1
    total_pages = math.ceil(total_filtered / max_btn)
    temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = page_files
    temp.CHAT[query.from_user.id] = query.message.chat.id
    settings = await get_settings(query.message.chat.id)

    cap = CAP.get(key, "")
    del_msg = f"\n\n<b>⚠️ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴀꜰᴛᴇʀ <code>{get_readable_time(DELETE_TIME)}</code> ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs</b>" if settings.get("auto_delete") else ""

    if settings.get("link"):
        links = "".join([
            f"<b>\n\n{i}. <a href=https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{f['_id']}>[{get_size(f['file_size'])}] {' '.join(filter(lambda x: not any(x.startswith(p) for p in ['[', '@', 'www.']), f['file_name'].split()))}</a></b>"
            for i, f in enumerate(page_files, current_offset + 1)
        ])
        btn = []
    else:
        links = ""
        btn = [[InlineKeyboardButton(f"🔗 {get_size(f['file_size'])}≽ {f.get('caption', formate_file_name(f['file_name']))}", callback_data=f"files#{query.from_user.id}#{f['_id']}")] for f in page_files]

    btn.insert(0, [
        InlineKeyboardButton("• ǫᴜᴀʟɪᴛʏ •", callback_data=f"qualities#{key}#{current_offset}#{req}"),
        InlineKeyboardButton("• ʟᴀɴɢᴜᴀɢᴇ •", callback_data=f"languages#{key}#{current_offset}#{req}")
    ])
    btn.insert(1, [InlineKeyboardButton("• sᴇɴᴅ ᴀʟʟ •", callback_data=f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}")])

    nav_row = []
    if current_offset > 0:
        nav_row.append(InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"season_search#{season}#{key}#{max(0, current_offset - max_btn)}#{original_offset}#{req}"))
    nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="pages"))
    if current_offset + max_btn < total_filtered:
        nav_row.append(InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"season_search#{season}#{key}#{current_offset + max_btn}#{original_offset}#{req}"))

    btn.append(nav_row if len(nav_row) > 1 else [InlineKeyboardButton("🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="buttons")])
    btn.append([InlineKeyboardButton("⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{original_offset}")])

    await query.message.edit_text(cap + links + del_msg, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))

@Client.on_callback_query(filters.regex(r"^qualities#"))
async def quality_cb_handler(client: Client, query: CallbackQuery):
    _, key, offset, req = query.data.split("#")
    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)

    btn = []
    for i in range(0, len(QUALITIES), 2):
        row = [InlineKeyboardButton(QUALITIES[i].title(), callback_data=f"quality_search#{QUALITIES[i].lower()}#{key}#0#{offset}#{req}")]
        if i + 1 < len(QUALITIES):
            row.append(InlineKeyboardButton(QUALITIES[i+1].title(), callback_data=f"quality_search#{QUALITIES[i+1].lower()}#{key}#0#{offset}#{req}"))
        btn.append(row)

    btn.append([InlineKeyboardButton("⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_0")])

    await query.message.edit_text(
        "<b>ɪɴ ᴡʜɪᴄʜ ǫᴜᴀʟɪᴛʏ ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ, ᴄʜᴏᴏsᴇ ꜰʀᴏᴍ ʜᴇʀᴇ ↓↓</b>", 
        reply_markup=InlineKeyboardMarkup(btn)
    )

@Client.on_callback_query(filters.regex(r"^quality_search#"))
async def quality_search(client: Client, query: CallbackQuery):
    _, qul, key, offset, original_offset, req = query.data.split("#")

    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)

    search = BUTTONS.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    current_offset = int(offset)
    max_btn = int(MAX_BTN)

    all_files, search_offset = [], 0
    while True:
        batch_files, next_offset, _ = await get_search_results(search.replace("_", " "), max_btn, search_offset)
        if not batch_files:
            break
        all_files.extend(batch_files)
        search_offset = int(next_offset) if next_offset else None
        if not search_offset:
            break

    filtered_files = [f for f in all_files if re.search(qul, f['file_name'], re.IGNORECASE)]

    if not filtered_files:
        return await query.answer(f"sᴏʀʀʏ {qul.title()} ɴᴏᴛ ꜰᴏᴜɴᴅ ꜰᴏʀ {search.replace('_', ' ')}", show_alert=True)

    page_files = filtered_files[current_offset:current_offset + max_btn]
    total_filtered = len(filtered_files)
    current_page = (current_offset // max_btn) + 1
    total_pages = math.ceil(total_filtered / max_btn)
    temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = page_files
    temp.CHAT[query.from_user.id] = query.message.chat.id
    settings = await get_settings(query.message.chat.id)

    cap = CAP.get(key, "")
    del_msg = f"\n\n<b>⚠️ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴀꜰᴛᴇʀ <code>{get_readable_time(DELETE_TIME)}</code> ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs</b>" if settings.get("auto_delete") else ""

    if settings.get("link"):
        links = "".join([
            f"<b>\n\n{i}. <a href=https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{f['_id']}>[{get_size(f['file_size'])}] {' '.join(filter(lambda x: not any(x.startswith(p) for p in ['[', '@', 'www.']), f['file_name'].split()))}</a></b>"
            for i, f in enumerate(page_files, current_offset + 1)
        ])
        btn = []
    else:
        links = ""
        btn = [[InlineKeyboardButton(f"🔗 {get_size(f['file_size'])}≽ {f.get('caption', formate_file_name(f['file_name']))}", callback_data=f"files#{query.from_user.id}#{f['_id']}")] for f in page_files]

    btn.insert(0, [
        InlineKeyboardButton("• ʟᴀɴɢᴜᴀɢᴇ •", callback_data=f"languages#{key}#{current_offset}#{req}"),
        InlineKeyboardButton("• sᴇᴀsᴏɴ •", callback_data=f"seasons#{key}#{current_offset}#{req}")
    ])
    btn.insert(1, [InlineKeyboardButton("• sᴇɴᴅ ᴀʟʟ •", callback_data=f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}")])

    nav_row = []
    if current_offset > 0:
        nav_row.append(InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"quality_search#{qul}#{key}#{max(0, current_offset - max_btn)}#{original_offset}#{req}"))
    nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="pages"))
    if current_offset + max_btn < total_filtered:
        nav_row.append(InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"quality_search#{qul}#{key}#{current_offset + max_btn}#{original_offset}#{req}"))

    btn.append(nav_row if len(nav_row) > 1 else [InlineKeyboardButton("🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="buttons")])
    btn.append([InlineKeyboardButton("⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{original_offset}")])

    await query.message.edit_text(cap + links + del_msg, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))

@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_cb_handler(client: Client, query: CallbackQuery):
    try:
        _, key, offset, req = query.data.split("#")
        if int(req) != query.from_user.id:
            return await query.answer(script.ALRT_TXT, show_alert=True)

        btn = []
        for i in range(0, len(LANGUAGES), 2):
            row = [InlineKeyboardButton(LANGUAGES[i][0], callback_data=f"lang_search#{LANGUAGES[i][1]}#{key}#0#{offset}#{req}")]
            if i + 1 < len(LANGUAGES):
                row.append(InlineKeyboardButton(LANGUAGES[i+1][0], callback_data=f"lang_search#{LANGUAGES[i+1][1]}#{key}#0#{offset}#{req}"))
            btn.append(row)

        btn.append([InlineKeyboardButton("⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_0")])

        await query.message.edit_text(
            "<b>ɪɴ ᴡʜɪᴄʜ ʟᴀɴɢᴜᴀɢᴇ ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ, ᴄʜᴏᴏsᴇ ꜰʀᴏᴍ ʜᴇʀᴇ ↓↓</b>", 
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except Exception as e:
        await query.answer("Error processing request", show_alert=True)

@Client.on_callback_query(filters.regex(r"^lang_search#"))
async def lang_search(client: Client, query: CallbackQuery):
    _, lang, key, offset, original_offset, req = query.data.split("#")

    if int(req) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)

    search = BUTTONS.get(key)
    if not search:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)

    current_offset = int(offset)
    max_btn = int(MAX_BTN)
    lang_patterns = [lang, lang[:3]]

    all_files, search_offset = [], 0
    while True:
        batch_files, next_offset, _ = await get_search_results(search.replace("_", " "), max_btn, search_offset)
        if not batch_files:
            break
        all_files.extend(batch_files)
        search_offset = int(next_offset) if next_offset else None
        if not search_offset:
            break

    filtered_files = [f for f in all_files if any(re.search(p, f['file_name'], re.IGNORECASE) for p in lang_patterns)]

    if not filtered_files:
        return await query.answer(f"sᴏʀʀʏ ʟᴀɴɢᴜᴀɢᴇ {lang.title()} ɴᴏᴛ ꜰᴏᴜɴᴅ ꜰᴏʀ {search.replace('_', ' ')}", show_alert=True)

    page_files = filtered_files[current_offset:current_offset + max_btn]
    total_filtered = len(filtered_files)
    current_page = (current_offset // max_btn) + 1
    total_pages = math.ceil(total_filtered / max_btn)
    temp.FILES_ID[f"{query.message.chat.id}-{query.id}"] = page_files
    temp.CHAT[query.from_user.id] = query.message.chat.id
    settings = await get_settings(query.message.chat.id)

    cap = CAP.get(key, "")
    del_msg = f"\n\n<b>⚠️ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴀꜰᴛᴇʀ <code>{get_readable_time(DELETE_TIME)}</code> ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs</b>" if settings.get("auto_delete") else ""

    if settings.get("link"):
        links = "".join([
            f"<b>\n\n{i}. <a href=https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{f['_id']}>[{get_size(f['file_size'])}] {' '.join(filter(lambda x: not any(x.startswith(p) for p in ['[', '@', 'www.']), f['file_name'].split()))}</a></b>"
            for i, f in enumerate(page_files, current_offset + 1)
        ])
        btn = []
    else:
        links = ""
        btn = [[InlineKeyboardButton(f"🔗 {get_size(f['file_size'])}≽ {f.get('caption', formate_file_name(f['file_name']))}", callback_data=f"files#{query.from_user.id}#{f['_id']}")] for f in page_files]

    btn.insert(0, [
        InlineKeyboardButton("• sᴇᴀsᴏɴ •", callback_data=f"seasons#{key}#{current_offset}#{req}"),
        InlineKeyboardButton("• ǫᴜᴀʟɪᴛʏ •", callback_data=f"qualities#{key}#{current_offset}#{req}")
    ])
    btn.insert(1, [InlineKeyboardButton("• sᴇɴᴅ ᴀʟʟ •", callback_data=f"batchfiles#{query.message.chat.id}#{query.id}#{query.from_user.id}")])

    nav_row = []
    if current_offset > 0:
        nav_row.append(InlineKeyboardButton("⪻ ʙᴀᴄᴋ", callback_data=f"lang_search#{lang}#{key}#{max(0, current_offset - max_btn)}#{original_offset}#{req}"))
    nav_row.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="pages"))
    if current_offset + max_btn < total_filtered:
        nav_row.append(InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"lang_search#{lang}#{key}#{current_offset + max_btn}#{original_offset}#{req}"))

    btn.append(nav_row if len(nav_row) > 1 else [InlineKeyboardButton("🚸 ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 🚸", callback_data="buttons")])
    btn.append([InlineKeyboardButton("⪻ ʙᴀᴄᴋ ᴛᴏ ᴍᴀɪɴ ᴘᴀɢᴇ", callback_data=f"next_{req}_{key}_{original_offset}")])

    await query.message.edit_text(cap + links + del_msg, disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML, reply_markup=InlineKeyboardMarkup(btn))

@Client.on_callback_query(filters.regex(r"^spol"))
async def spoll_checker(bot, query):
    _, id, user = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT, show_alert=True)
    movie = await get_poster(id, id=True)
    search = movie.get('title')
    await query.answer('ᴄʜᴇᴄᴋɪɴɢ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀꜱᴇ 🌚')
    files, offset, total_results = await get_search_results(search)
    if files:
        k = (search, files, offset, total_results)
        await auto_filter(bot, query, k)
    else:
        try:
            await bot.send_message(
                LOG_CHANNEL,
                f"📢 No results found!\n\n🔹 Query: <b>{search}</b>\n🔹 User ID: <code>{query.from_user.id}</code>\n🔹 Username: @{query.from_user.username if query.from_user.username else 'N/A'}",
                parse_mode="html"
            )
        except Exception as e:
            print(f"Failed to send log: {e}")

        buttons = [[
            InlineKeyboardButton("⚠️ ʀᴇᴏ̨ᴜᴇsᴛ ᴛᴏ ᴀᴅᴍɪɴ ⚠️", callback_data=f"req_admin#{search}#{query.from_user.id}")
        ], [
            InlineKeyboardButton("🚫 ᴄʟᴏsᴇ 🚫", callback_data="close_data")
        ]]
        await query.message.edit(
            script.NO_RESULT_TXT,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await asyncio.sleep(60)
        try:
            await query.message.delete()
        except:
            pass

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):

    if query.data == "close_data":
        try:
            user = query.message.reply_to_message.from_user.id
        except:
            user = query.from_user.id
        if int(user) != 0 and query.from_user.id != int(user):
            return await query.answer(script.ALRT_TXT, show_alert=True)
        await query.answer("ᴛʜᴀɴᴋs ꜰᴏʀ ᴄʟᴏsᴇ 🙈")
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
           pass

    elif query.data == "premium":
        userid = query.from_user.id
        await query.message.reply_photo(
            photo=QR_CODE,
            caption=script.PREMIUM_TEXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('🎁 ʀᴇꜰᴇʀ ᴛᴏ ɢᴇᴛ ᴘʀᴇᴍɪᴜᴍ 🎁', callback_data='reff')],
                [InlineKeyboardButton('ᴄʟᴏsᴇ', callback_data='close_data')]
            ]))

    elif query.data == "reff":
        refer_link = f"https://t.me/{temp.U_NAME}?start=reff_{query.from_user.id}"
        btn = [
            [InlineKeyboardButton('ɪɴᴠɪᴛᴇ ʟɪɴᴋ', url=f'https://telegram.me/share/url?url={refer_link}&text=Hello!%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83'),
            InlineKeyboardButton(f'⏳ {silicondb.get_silicon_refer_points(query.from_user.id)}', callback_data='ref_point'),
            InlineKeyboardButton('ᴄʟᴏsᴇ', callback_data='close_data')]
        ]
        reply_markup = InlineKeyboardMarkup(btn)

        await query.message.reply_photo(
            photo="https://graph.org/file/1a2e64aee3d4d10edd930.jpg",
            caption=(
                f'Hey Your refer link:\n\n{refer_link}\n\n'
                'Share this link with your friends, Each time they join,  you will get 10 refer points and '
                'after 100 points you will get 1 month premium subscription.'
            ),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer()

    elif query.data == "ref_point":
        await query.answer(f'You Have: {silicondb.get_silicon_refer_points(query.from_user.id)} Refferal points.', show_alert=True)

    elif query.data == "top_search":
        searches = await process_trending_data(limit=20, format_type="keyboard")
        keyboard = create_keyboard_layout(searches)

        reply_markup = ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            resize_keyboard=True,
            placeholder="ᴍᴏsᴛ sᴇᴀʀᴄʜᴇs ᴏꜰ ᴛʜᴇ ᴅᴀʏ"
        )
        await query.message.reply_text(
            "<b>ᴛᴏᴘ sᴇᴀʀᴄʜᴇs ᴏꜰ ᴛʜᴇ ᴅᴀʏ 👇</b>", 
            reply_markup=reply_markup
        )
        await query.answer()

    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type
        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()
        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)    

    elif query.data.startswith("checksub"):
        try:
            ident, kk, file_id = query.data.split("#")
            btn = []
            chat = file_id.split("_")[0]
            settings = await get_settings(chat)
            fsub_channels = list(dict.fromkeys((settings.get('fsub', []) if settings else [])+ AUTH_CHANNELS)) 
            btn += await is_subscribed(client, query.from_user.id, fsub_channels)
            btn += await is_req_subscribed(client, query.from_user.id, AUTH_REQ_CHANNELS)
            if btn:
                btn.append([InlineKeyboardButton("♻️ ᴛʀʏ ᴀɢᴀɪɴ ♻️", callback_data=f"checksub#{kk}#{file_id}")])
                try:
                    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
                except MessageNotModified:
                    pass
                await query.answer(
                    f"👋 ʜᴇʟʟᴏ {query.from_user.first_name},\n\n"
                    "🛑 ʏᴏᴜ ʜᴀᴠᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ᴀʟʟ ʀᴇǫᴜɪʀᴇᴅ ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟs.\n"
                    "👉 ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴇᴀᴄʜ ᴏɴᴇ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.\n",
                    show_alert=True
                )
                return
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={kk}_{file_id}")
            await query.message.delete()
        except Exception as e:
            await log_error(client, f"❌ Error in checksub callback:\n\n{repr(e)}")
            logger.error(f"❌ Error in checksub callback:\n\n{repr(e)}")

    elif query.data == "buttons":
        await query.answer("ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs 😊", show_alert=True)

    elif query.data == "pages":
        await query.answer("ᴛʜɪs ɪs ᴘᴀɢᴇs ʙᴜᴛᴛᴏɴ 😅")

    elif query.data.startswith("lang_art"):
        _, lang = query.data.split("#")
        await query.answer(f"ʏᴏᴜ sᴇʟᴇᴄᴛᴇᴅ {lang.title()} ʟᴀɴɢᴜᴀɢᴇ ⚡️", show_alert=True)

    elif query.data == "start":
        buttons = [
            [
                InlineKeyboardButton('⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs ⇆', url=f'http://t.me/{temp.U_NAME}?startgroup=start')
            ],
            [
                InlineKeyboardButton('• ꜰᴇᴀᴛᴜʀᴇs', callback_data='features'),
                InlineKeyboardButton('• ᴜᴘɢʀᴀᴅᴇ', callback_data='premium')
            ],
            [
                InlineKeyboardButton('• ᴛᴏᴘ', callback_data='top_search'),
                InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about')
            ],
            [
                InlineKeyboardButton('• ᴇᴀʀɴ ᴍᴏɴᴇʏ ᴡɪᴛʜ ʙᴏᴛ •', callback_data='earn')]
            ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, get_status(), query.from_user.id),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )   

    elif query.data.startswith("stream"):
        file_id = query.data.split('#', 1)[1]

        if IS_PREMIUM_STREAM:
            if not await db.has_premium_access(query.from_user.id):
                await query.answer(
                    "⚠️ ᴘʀᴇᴍɪᴜᴍ ᴄᴏɴᴛᴇɴᴛ ❗\n🔓 ᴜɴʟᴏᴄᴋ ɪᴛ ʙʏ ᴜᴘɢʀᴀᴅɪɴɢ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ",
                    show_alert=True
                )
                await query.message.reply_text(
                    "🔒 ᴛʜɪs ꜰᴇᴀᴛᴜʀᴇ ɪs ᴏɴʟʏ ꜰᴏʀ 🏅 ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs\n\n"
                    "✨ ᴜɴʟᴏᴄᴋ ᴇxᴄʟᴜsɪᴠᴇ ᴄᴏɴᴛᴇɴᴛ ᴀɴᴅ ꜰᴇᴀᴛᴜʀᴇs\n"
                    "💳 ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ ᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ"
                )
                return

        silicon = await client.send_cached_media(chat_id=BIN_CHANNEL, file_id=file_id)
        watch = f"{URL}watch/{silicon.id}"
        download = f"{URL}download/{silicon.id}"
        btn = [
            [
                InlineKeyboardButton("ᴡᴀᴛᴄʜ ᴏɴʟɪɴᴇ", url=watch),
                InlineKeyboardButton("ꜰᴀsᴛ ᴅᴏᴡɴʟᴏᴀᴅ", url=download)
            ],
            [
                InlineKeyboardButton('❌ ᴄʟᴏsᴇ ❌', callback_data='close_data')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(btn)
        await query.edit_message_reply_markup(
            reply_markup=reply_markup
        )

    elif query.data == "features":
        buttons = [[
            InlineKeyboardButton('📸 ᴛ-ɢʀᴀᴘʜ', callback_data='telegraph'),
            InlineKeyboardButton('🆎️ ꜰᴏɴᴛ', callback_data='font')    
        ],
        [
          InlineKeyboardButton('🛢 ɢʀᴏᴜᴘ ᴄᴍᴅ', callback_data='grp_cmd'),
          InlineKeyboardButton('🧾 ᴀᴅᴍɪɴ ᴄᴍᴅ', callback_data='admincmd')
        ],
        [
              InlineKeyboardButton('⋞ ʜᴏᴍᴇ', callback_data='start')
        ]] 
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(                     
            text=script.HELP_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "admincmd":
        if not query.from_user.id in ADMINS:
            return await query.answer('ᴛʜɪs ꜰᴇᴀᴛᴜʀᴇ ɪs ᴏɴʟʏ ꜰᴏʀ ᴀᴅᴍɪɴs !' , show_alert=True)
        buttons = [
            [InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='features')],
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ADMIN_CMD_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML,
        )
    elif query.data == "grp_cmd":
        buttons = [[
            InlineKeyboardButton('⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs ⇆', url=f'http://t.me/{temp.U_NAME}?startgroup=start')],
            [InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='features')]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GROUP_CMD,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == 'about':
        await query.message.edit_text(
            script.ABOUT_TEXT.format(temp.B_LINK),
            reply_markup = InlineKeyboardMarkup(
                [[
            InlineKeyboardButton ('🎁 sᴏᴜʀᴄᴇ', callback_data='source'),
            InlineKeyboardButton ('📖 ᴅᴍᴄᴀ', callback_data='dmca')
        ],[
            InlineKeyboardButton('⋞ ʜᴏᴍᴇ', callback_data='start')]]
                ),
            disable_web_page_preview = True
        )

    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('ꜱᴏᴜʀᴄᴇ ᴄᴏᴅᴇ 📜', url='https://github.com/Silicon-Developer/Auto-Filter-Bot.git'),
            InlineKeyboardButton('⇋ ʙᴀᴄᴋ ⇋', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "dmca":
            btn = [[
                    InlineKeyboardButton("⇋ ʙᴀᴄᴋ ⇋", callback_data="about")
                  ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.DISCLAIMER_TXT),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML 
            )

    elif query.data == "earn":
        buttons = [[
            InlineKeyboardButton('⋞ ʜᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ', user_id = ADMINS[0] ),
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
             text=script.EARN_TEXT.format(temp.B_LINK),
             reply_markup=reply_markup,
             parse_mode=enums.ParseMode.HTML
         )
    elif query.data == "telegraph":
        buttons = [[
            InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='features')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)  
        await query.message.edit_text(
            text=script.TELE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "font":
        buttons = [[
            InlineKeyboardButton('⋞ ʙᴀᴄᴋ', callback_data='features')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons) 
        await query.message.edit_text(
            text=script.FONT_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "all_files_delete":
        files_primary = collection.count_documents({})

        files_secondary = 0
        if is_second_db_configured():
            files_secondary = second_collection.count_documents({})

        total_files = files_primary + files_secondary

        try:
            collection.drop()
        except Exception as e:
            logger.error(f"Error dropping main collection: {e}")

        if is_second_db_configured():
            try:
                second_collection.drop()
            except Exception as e:
                logger.error(f"Error dropping second collection: {e}")

        await query.answer('ᴅᴇʟᴇᴛɪɴɢ...')
        await query.message.edit_text(f"sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ {total_files} ꜰɪʟᴇs")

    elif query.data.startswith("delete"):
        _, query_ = query.data.split("_", 1)
        await query.message.edit('ᴅᴇʟᴇᴛɪɴɢ...')
        deleted = await delete_files(query_)
        await query.message.edit(f'ᴅᴇʟᴇᴛᴇᴅ {deleted} ꜰɪʟᴇs ɪɴ ʏᴏᴜʀ ᴅᴀᴛᴀʙᴀsᴇ ɪɴ ʏᴏᴜʀ ǫᴜᴇʀʏ {query_}')

    elif query.data.startswith("reset_grp_data"):
        grp_id = query.message.chat.id
        btn = [[
            InlineKeyboardButton('☕️ ᴄʟᴏsᴇ ☕️', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(btn)

        await save_group_settings(grp_id, 'shortner', SHORTENER_WEBSITE)
        await save_group_settings(grp_id, 'api', SHORTENER_API)
        await save_group_settings(grp_id, 'shortner_two', SHORTENER_WEBSITE2)
        await save_group_settings(grp_id, 'api_two', SHORTENER_API2)
        await save_group_settings(grp_id, 'shortner_three', SHORTENER_WEBSITE3)
        await save_group_settings(grp_id, 'api_three', SHORTENER_API3)
        await save_group_settings(grp_id, 'template', IMDB_TEMPLATE)
        await save_group_settings(grp_id, 'tutorial', TUTORIAL)
        await save_group_settings(grp_id, 'tutorial_two', TUTORIAL2)
        await save_group_settings(grp_id, 'tutorial_three', TUTORIAL3)
        await save_group_settings(grp_id, 'caption', FILE_CAPTION)
        await save_group_settings(grp_id, 'log', LOG_VR_CHANNEL)
        await save_group_settings(grp_id, 'fsub', [])
        await save_group_settings(grp_id, 'auto_filter', True)
        await save_group_settings(grp_id, 'spell_check', True)
        await save_group_settings(grp_id, 'imdb', True) 
        await save_group_settings(grp_id, 'link', True) 
        await save_group_settings(grp_id, 'is_verify', True)  
        await save_group_settings(grp_id, 'auto_delete', True)

        await query.answer('ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʀᴇꜱᴇᴛ...')
        await query.message.edit_text(
            "<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʀᴇꜱᴇᴛ ɢʀᴏᴜᴘ ꜱᴇᴛᴛɪɴɢꜱ...\n\nɴᴏᴡ ꜱᴇɴᴅ /details ᴀɢᴀɪɴ</b>",
            reply_markup=reply_markup
        )

    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            await query.answer(script.ALRT_TXT, show_alert=True)
            return
        if status == "True":
            await save_group_settings(int(grp_id), set_type, False)
            await query.answer("ᴏꜰꜰ ❌")
        else:
            await save_group_settings(int(grp_id), set_type, True)
            await query.answer("ᴏɴ ✅")
        settings = await get_settings(int(grp_id))      
        if settings is not None:
            buttons = [[
                InlineKeyboardButton('ᴀᴜᴛᴏ ꜰɪʟᴛᴇʀ', callback_data=f'setgs#auto_filter#{settings["auto_filter"]}#{grp_id}'),
                InlineKeyboardButton('ᴏɴ ✓' if settings["auto_filter"] else 'ᴏꜰꜰ ✗', callback_data=f'setgs#auto_filter#{settings["auto_filter"]}#{grp_id}')
            ],[
                InlineKeyboardButton('ɪᴍᴅʙ', callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}'),
                InlineKeyboardButton('ᴏɴ ✓' if settings["imdb"] else 'ᴏꜰꜰ ✗', callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}')
            ],[
                InlineKeyboardButton('sᴘᴇʟʟ ᴄʜᴇᴄᴋ', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}'),
                InlineKeyboardButton('ᴏɴ ✓' if settings["spell_check"] else 'ᴏꜰꜰ ✗', callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}')
            ],[
                InlineKeyboardButton('ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ', callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}'),
                InlineKeyboardButton(f'{get_readable_time(DELETE_TIME)}' if settings["auto_delete"] else 'ᴏꜰꜰ ✗', callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}')
            ],[
                InlineKeyboardButton('ʀᴇsᴜʟᴛ ᴍᴏᴅᴇ', callback_data=f'setgs#link#{settings["link"]}#{str(grp_id)}'),
                InlineKeyboardButton('⛓ ʟɪɴᴋ' if settings["link"] else '🧲 ʙᴜᴛᴛᴏɴ', callback_data=f'setgs#link#{settings["link"]}#{str(grp_id)}')
            ],[
                InlineKeyboardButton('ᴠᴇʀɪꜰʏ', callback_data=f'setgs#is_verify#{settings["is_verify"]}#{grp_id}'),
                InlineKeyboardButton('ᴏɴ ✓' if settings["is_verify"] else 'ᴏꜰꜰ ✗', callback_data=f'setgs#is_verify#{settings["is_verify"]}#{grp_id}')
            ],[
                InlineKeyboardButton('❌ ᴄʟᴏsᴇ ❌', callback_data='close_data')
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
            d = await query.message.edit_reply_markup(reply_markup)
            await asyncio.sleep(300)
            await d.delete()
        else:
            await query.message.edit_text("<b>ꜱᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ</b>")

    elif query.data.startswith("group_pm"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        btn = await group_setting_buttons(int(grp_id)) 
        gt = await client.get_chat(int(grp_id))
        await query.message.edit(
            text=(
                f"ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ꜱᴇᴛᴛɪɴɢꜱ ✅\n\n"
                f"ɢʀᴏᴜᴘ ɴᴀᴍᴇ - {gt.title} ⚙ \n"
                f"ɢʀᴏᴜᴘ ɪᴅ - <code>{gt.id}</code> "
            ),
            reply_markup=InlineKeyboardMarkup(btn)
        )

    elif query.data.startswith("batchfiles"):
        ident, group_id, message_id, user = query.data.split("#")
        group_id = int(group_id)
        message_id = int(message_id)
        user = int(user)
        if user != query.from_user.id:
            await query.answer(script.ALRT_TXT, show_alert=True)
            return
        link = f"https://telegram.me/{temp.U_NAME}?start=allfiles_{group_id}-{message_id}"
        await query.answer(url=link)
        return

    elif query.data.startswith("show_options"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("✅️ ᴀᴄᴄᴇᴘᴛ ᴛʜɪꜱ ʀᴇǫᴜᴇꜱᴛ ✅️", callback_data=f"accept#{user_id}#{msg_id}")
        ],[
            InlineKeyboardButton("🚫 ʀᴇᴊᴇᴄᴛ ᴛʜɪꜱ ʀᴇǫᴜᴇꜱᴛ 🚫", callback_data=f"reject#{user_id}#{msg_id}")
        ]]
        try:
            st = await client.get_chat_member(chnl_id, userid)
            if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
                await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            elif st.status == enums.ChatMemberStatus.MEMBER:
                await query.answer(script.ALRT_TXT, show_alert=True)
        except pyrogram.errors.exceptions.bad_request_400.UserNotParticipant:
            await query.answer("⚠️ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀ ᴍᴇᴍʙᴇʀ ᴏꜰ ᴛʜɪꜱ ᴄʜᴀɴɴᴇʟ, ꜰɪʀꜱᴛ ᴊᴏɪɴ", show_alert=True)

    elif query.data.startswith("reject"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("✗ ʀᴇᴊᴇᴄᴛ ✗", callback_data=f"rj_alert#{user_id}")
        ]]
        btn = [[
            InlineKeyboardButton("♻️ ᴠɪᴇᴡ sᴛᴀᴛᴜs ♻️", url=f"{query.message.link}")
        ]]
        st = await client.get_chat_member(chnl_id, userid)
        if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
            user = await client.get_users(user_id)
            request = query.message.text
            await query.answer("Message sent to requester")
            await query.message.edit_text(f"<s>{request}</s>")
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            try:
                await client.send_message(chat_id=user_id, text="<b>sᴏʀʀʏ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪs ʀᴇᴊᴇᴄᴛᴇᴅ 😶</b>", reply_markup=InlineKeyboardMarkup(btn))
            except UserIsBlocked:
                await client.send_message(SUPPORT_GROUP, text=f"<b>💥 ʜᴇʟʟᴏ {user.mention},\n\nsᴏʀʀʏ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪs ʀᴇᴊᴇᴄᴛᴇᴅ 😶</b>", reply_markup=InlineKeyboardMarkup(btn), reply_to_message_id=int(msg_id))
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("accept"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("😊 ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ 😊", callback_data=f"already_available#{user_id}#{msg_id}")
        ],[
            InlineKeyboardButton("‼️ ɴᴏᴛ ʀᴇʟᴇᴀsᴇᴅ ʏᴇᴛ ‼️", callback_data=f"not_available#{user_id}#{msg_id}")
        ],[
            InlineKeyboardButton("🥵 ᴛᴇʟʟ ᴍᴇ ʏᴇᴀʀ/ʟᴀɴɢᴜᴀɢᴇ 🥵", callback_data=f"year#{user_id}#{msg_id}")
        ],[
            InlineKeyboardButton("⚠️ ᴅᴜᴅᴇ, ᴄʜᴇᴄᴋ ʏᴏᴜʀ sᴘᴇʟʟɪɴɢ ⚠️", callback_data=f"upload_in#{user_id}#{msg_id}")
        ],[
            InlineKeyboardButton("☇ ᴜᴘʟᴏᴀᴅᴇᴅ ☇", callback_data=f"uploaded#{user_id}#{msg_id}")
        ],[
            InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data=f"show_options#{ident}#{user_id}#{msg_id}")
        ]]
        try:
            st = await client.get_chat_member(chnl_id, userid)
            if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
                await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            elif st.status == enums.ChatMemberStatus.MEMBER:
                await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        except pyrogram.errors.exceptions.bad_request_400.UserNotParticipant:
            await query.answer("⚠️ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀ ᴍᴇᴍʙᴇʀ ᴏꜰ ᴛʜɪꜱ ᴄʜᴀɴɴᴇʟ, ꜰɪʀꜱᴛ ᴊᴏɪɴ", show_alert=True)

    elif query.data.startswith("not_available"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("🚫 ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ 🚫", callback_data=f"na_alert#{user_id}")
        ]]
        btn = [[
            InlineKeyboardButton("♻️ ᴠɪᴇᴡ sᴛᴀᴛᴜs ♻️", url=f"{query.message.link}")
        ]]
        st = await client.get_chat_member(chnl_id, userid)
        if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
            user = await client.get_users(user_id)
            request = query.message.text
            await query.answer("Message sent to requester")
            await query.message.edit_text(f"<s>{request}</s>")
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            try:
                await client.send_message(chat_id=user_id, text="<b>sᴏʀʀʏ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪs ɴᴏᴛ ʀᴇʟᴇᴀsᴇᴅ ʏᴇᴛ 😢.\n ᴀᴅᴍɪɴ ᴋᴇᴇᴘ ᴍᴏɴɪᴛᴏʀ ʏᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ, ᴡᴀɪᴛ ғᴏʀ ʀᴇʟᴇᴀsᴇ ᴀɴᴅ ᴛʜᴇɴ sᴇɴᴅ ʀᴇᴏ̨ᴜᴇsᴛᴇᴅ ғɪʟᴇ ɴᴀᴍᴇ ɪɴ ɢʀᴏᴜᴘ.</b>", reply_markup=InlineKeyboardMarkup(btn))
            except UserIsBlocked:
                await client.send_message(SUPPORT_GROUP, text=f"<b>💥 ʜᴇʟʟᴏ {user.mention},\n\nsᴏʀʀʏ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪs ɴᴏᴛ ʀᴇʟᴇᴀsᴇᴅ ʏᴇᴛ 😢.\n ᴀᴅᴍɪɴ ᴋᴇᴇᴘ ᴍᴏɴɪᴛᴏʀ ʏᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ, ᴡᴀɪᴛ ғᴏʀ ʀᴇʟᴇᴀsᴇ ᴀɴᴅ ᴛʜᴇɴ sᴇɴᴅ ʀᴇᴏ̨ᴜᴇsᴛᴇᴅ ғɪʟᴇ ɴᴀᴍᴇ ɪɴ ɢʀᴏᴜᴘ.</b>", reply_markup=InlineKeyboardMarkup(btn), reply_to_message_id=int(msg_id))
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("uploaded"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("🙂 ᴜᴘʟᴏᴀᴅᴇᴅ 🙂", callback_data=f"ul_alert#{user_id}")
        ]]
        btn = [[
            InlineKeyboardButton("♻️ ᴠɪᴇᴡ sᴛᴀᴛᴜs ♻️", url=f"{query.message.link}")
        ]]
        st = await client.get_chat_member(chnl_id, userid)
        if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
            user = await client.get_users(user_id)
            request = query.message.text
            await query.answer("Message sent to requester")
            await query.message.edit_text(f"<s>{request}</s>")
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            try:
                await client.send_message(chat_id=user_id, text="<b>ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪs ᴜᴘʟᴏᴀᴅᴇᴅ ☺️, ᴊᴜsᴛ ʀᴇ-sᴇɴᴅ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ɪɴ ɢʀᴏᴜᴘ</b>", reply_markup=InlineKeyboardMarkup(btn))
            except UserIsBlocked:
                await client.send_message(SUPPORT_GROUP, text=f"<b>💥 ʜᴇʟʟᴏ {user.mention},\n\nʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪs ᴜᴘʟᴏᴀᴅᴇᴅ ☺️, ᴊᴜsᴛ ʀᴇ-sᴇɴᴅ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ɪɴ ɢʀᴏᴜᴘ</b>", reply_markup=InlineKeyboardMarkup(btn), reply_to_message_id=int(msg_id))
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("already_available"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("🫤 ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ 🫤", callback_data=f"aa_alert#{user_id}")
        ]]
        btn = [[
            InlineKeyboardButton("♻️ ᴠɪᴇᴡ sᴛᴀᴛᴜs ♻️", url=f"{query.message.link}")
        ]]
        st = await client.get_chat_member(chnl_id, userid)
        if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
            user = await client.get_users(user_id)
            request = query.message.text
            await query.answer("Message sent to requester")
            await query.message.edit_text(f"<s>{request}</s>")
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            try:
                await client.send_message(chat_id=user_id, text="<b>ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ 😋, ᴊᴜsᴛ ʀᴇ-sᴇɴᴅ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ɪɴ ɢʀᴏᴜᴘ</b>", reply_markup=InlineKeyboardMarkup(btn))
            except UserIsBlocked:
                await client.send_message(SUPPORT_GROUP, text=f"<b>💥 ʜᴇʟʟᴏ {user.mention},\n\nʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ 😋, ᴊᴜsᴛ ʀᴇ-sᴇɴᴅ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ɪɴ ɢʀᴏᴜᴘ</b>", reply_markup=InlineKeyboardMarkup(btn), reply_to_message_id=int(msg_id))
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("upload_in"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("⚠️ ᴄʜᴇᴄᴋ ʏᴏᴜʀ sᴘᴇʟʟɪɴɢ ⚠️", callback_data=f"upload_alert#{user_id}")
        ]]
        btn = [[
            InlineKeyboardButton("♻️ ᴠɪᴇᴡ sᴛᴀᴛᴜs ♻️", url=f"{query.message.link}")
        ]]
        st = await client.get_chat_member(chnl_id, userid)
        if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
            user = await client.get_users(user_id)
            request = query.message.text
            await query.answer("Message sent to requester")
            await query.message.edit_text(f"<s>{request}</s>")
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            try:
                await client.send_message(chat_id=user_id, text="<b>ᴀᴅᴍɪɴ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴀɴʏ ᴍᴏᴠɪᴇ ᴀɴᴅ sᴇʀɪᴇs ᴏғ ᴛʜɪs ɴᴀᴍᴇ \nᴍᴀᴋᴇ sᴜʀᴇ, ʏᴏᴜʀ sᴘᴇʟʟɪɴɢ ɪs ᴄᴏʀʀᴇᴄᴛ ⚠️. ᴄʜᴇᴄᴋ sᴘᴇʟʟɪɴɢ ᴏɴ ɢᴏᴏɢʟᴇ ᴀɴᴅ ᴛʜᴇɴ ʀᴇᴏ̨ᴜᴇsᴛ ᴀɢᴀɪɴ ❗</b>", reply_markup=InlineKeyboardMarkup(btn))
            except UserIsBlocked:
                await client.send_message(SUPPORT_GROUP, text=f"<b>💥 ʜᴇʟʟᴏ {user.mention},\n\nᴀᴅᴍɪɴ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴀɴʏ ᴍᴏᴠɪᴇ ᴀɴᴅ sᴇʀɪᴇs ᴏғ ᴛʜɪs ɴᴀᴍᴇ \nᴍᴀᴋᴇ sᴜʀᴇ, ʏᴏᴜʀ sᴘᴇʟʟɪɴɢ ɪs ᴄᴏʀʀᴇᴄᴛ ⚠️. ᴄʜᴇᴄᴋ sᴘᴇʟʟɪɴɢ ᴏɴ ɢᴏᴏɢʟᴇ ᴀɴᴅ ᴛʜᴇɴ ʀᴇᴏ̨ᴜᴇsᴛ ᴀɢᴀɪɴ ❗</b>", reply_markup=InlineKeyboardMarkup(btn), reply_to_message_id=int(msg_id))
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("year"):
        ident, user_id, msg_id = query.data.split("#")
        chnl_id = query.message.chat.id
        userid = query.from_user.id
        buttons = [[
            InlineKeyboardButton("⚠️ ᴛᴇʟʟ ᴍᴇ ʏᴇᴀʀꜱ & ʟᴀɴɢᴜᴀɢᴇ ⚠️", callback_data=f"yrs_alert#{user_id}")
        ]]
        btn = [[
            InlineKeyboardButton("♻️ ᴠɪᴇᴡ sᴛᴀᴛᴜs ♻️", url=f"{query.message.link}")
        ]]
        st = await client.get_chat_member(chnl_id, userid)
        if (st.status == enums.ChatMemberStatus.ADMINISTRATOR) or (st.status == enums.ChatMemberStatus.OWNER):
            user = await client.get_users(user_id)
            request = query.message.text
            await query.answer("Message sent to requester")
            await query.message.edit_text(f"<s>{request}</s>")
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            try:
                await client.send_message(chat_id=user_id, text="<b>ʙʀᴏ ᴘʟᴇᴀꜱᴇ ᴛᴇʟʟ ᴍᴇ ʏᴇᴀʀꜱ, ʟᴀɴɢᴜᴀɢᴇ, ʙᴏʟʟʏᴡᴏᴏᴅ ᴏʀ ʜᴏʟʟʏᴡᴏᴏᴅ ᴇᴛᴄ., ᴛʜᴇɴ ɪ ᴡɪʟʟ ᴜᴘʟᴏᴀᴅ 😬\n ᴊᴜsᴛ ʀᴇ-sᴇɴᴅ ʀᴇᴏ̨ᴜᴇsᴛ ᴡɪᴛʜ ᴍᴏʀᴇ ɪɴғᴏ.</b>", reply_markup=InlineKeyboardMarkup(btn))
            except UserIsBlocked:
                await client.send_message(SUPPORT_GROUP, text=f"<b>💥 ʜᴇʟʟᴏ {user.mention},\n\nʙʀᴏ ᴘʟᴇᴀꜱᴇ ᴛᴇʟʟ ᴍᴇ ʏᴇᴀʀꜱ, ʟᴀɴɢᴜᴀɢᴇ, ʙᴏʟʟʏᴡᴏᴏᴅ ᴏʀ ʜᴏʟʟʏᴡᴏᴏᴅ ᴇᴛᴄ., ᴛʜᴇɴ ɪ ᴡɪʟʟ ᴜᴘʟᴏᴀᴅ 😬\n ᴊᴜsᴛ ʀᴇ-sᴇɴᴅ ʀᴇᴏ̨ᴜᴇsᴛ ᴡɪᴛʜ ᴍᴏʀᴇ ɪɴғᴏ.</b>", reply_markup=InlineKeyboardMarkup(btn), reply_to_message_id=int(msg_id))
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("rj_alert"):
        ident, user_id = query.data.split("#")
        userid = query.from_user.id
        if str(userid) in user_id:
            await query.answer("sᴏʀʀʏ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪs ʀᴇᴊᴇᴄᴛ", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("na_alert"):
        ident, user_id = query.data.split("#")
        userid = query.from_user.id
        if str(userid) in user_id:
            await query.answer("sᴏʀʀʏ ʏᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ, ᴍᴀᴋᴇ sᴜʀᴇ ɪᴛ's ʀᴇʟᴇᴀsᴇᴅ. ɪғ ʏᴇs, ᴛʜᴇɴ ɢɪᴠᴇ ᴜs sᴏᴍᴇ ᴛɪᴍᴇ 🤗", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("ul_alert"):
        ident, user_id = query.data.split("#")
        userid = query.from_user.id
        if str(userid) in user_id:
            await query.answer("ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪs ᴜᴘʟᴏᴀᴅᴇᴅ", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("aa_alert"):
        ident, user_id = query.data.split("#")
        userid = query.from_user.id
        if str(userid) in user_id:
            await query.answer("ʏᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ, ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴄʜᴇᴄᴋ ғɪʀsᴛ ᴀɴᴅ ᴛʜᴇɴ ᴍᴀᴋᴇ ᴀ ʀᴇᴏ̨ᴜᴇsᴛ 🤨", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("upload_alert"):
        ident, user_id = query.data.split("#")
        userid = query.from_user.id
        if str(userid) in user_id:
            await query.answer("ʏᴏᴜ ᴜɴᴇᴅᴜᴄᴀᴛᴇᴅ, ᴄʜᴇᴄᴋ ʏᴏᴜʀ sᴘᴇʟʟɪɴɢ 😑", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

    elif query.data.startswith("yrs_alert"):
        ident, user_id = query.data.split("#")
        userid = query.from_user.id
        if str(userid) in user_id:
            await query.answer("ᴅᴜᴅᴇ ʏᴏᴜ ɴᴇᴇᴅ ᴛᴏ ᴘʀᴏᴠɪᴅᴇ ᴍᴏʀᴇ ɪɴғᴏ 😑 (ʟɪᴋᴇ : ʏᴇᴀʀ, ʟᴀɴɢᴜᴀɢᴇ, ʜᴏʟʟʏᴡᴏᴏᴅ ᴏʀ ʙᴏʟʟʏᴡᴏᴏᴅ)c", show_alert=True)
        else:
            await query.answer(script.ALRT_TXT, show_alert=True)

async def ai_spell_check(wrong_name):
    async def search_movie(wrong_name):
        search_results = imdb.search_movie(wrong_name)
        movie_list = [movie['title'] for movie in search_results]
        return movie_list
    movie_list = await search_movie(wrong_name)
    if not movie_list:
        return
    for _ in range(5):
        closest_match = process.extractOne(wrong_name, movie_list)
        if not closest_match or closest_match[1] <= 80:
            return 
        movie = closest_match[0]
        files, offset, total_results = await get_search_results(movie)
        if files:
            return movie
        movie_list.remove(movie)
    return

async def auto_filter(client, msg, spoll=False):
    if not spoll:
        message = msg
        search = message.text
        chat_id = message.chat.id
        search_msg = await msg.reply_text(f'<b>💦 sᴇᴀʀᴄʜɪɴɢ "{search}"</b>')

        settings = await get_settings(chat_id)
        files, offset, total_results = await get_search_results(search)
        silicondb.update_silicon_messages(message.from_user.id, message.text)

        await search_msg.delete()

        if not files:
            if settings["spell_check"]:
                ai_sts = await msg.reply_text('<b>ᴅᴇᴠɪʟ ᴄʜᴇᴄᴋɪɴɢ ꜰᴏʀ ʏᴏᴜʀ sᴘᴇʟʟɪɴɢ...</b>')
                is_misspelled = await ai_spell_check(search)
                if is_misspelled:
                    await ai_sts.edit(f'<b><i>ʏᴏᴜʀ ꜱᴘᴇʟʟɪɴɢ ɪꜱ ᴡʀᴏɴɢ ɴᴏᴡ ᴅᴇᴠɪʟ ꜱᴇᴀʀᴄʜɪɴɢ ᴡɪᴛʜ ᴄᴏʀʀᴇᴄᴛ ꜱᴘᴇʟʟɪɴɢ - <code>{is_misspelled}</code></i></b>')
                    await asyncio.sleep(2)
                    msg.text = is_misspelled
                    await ai_sts.delete()
                    return await auto_filter(client, msg)
                await ai_sts.delete()
                return await silicon_spell_check(msg)
            return
    else:
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message
        search, files, offset, total_results = spoll

    req = message.from_user.id if message.from_user else 0
    key = f"{message.chat.id}-{message.id}"

    temp.FILES_ID[key] = files
    temp.CHAT[message.from_user.id] = message.chat.id

    del_msg = f"\n\n<b>⚠️ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴀꜰᴛᴇʀ <code>{get_readable_time(DELETE_TIME)}</code> ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs</b>" if settings.get("auto_delete") else ""

    if settings.get("link"):
        links = "".join([
            f"<b>\n\n{i}. <a href=https://t.me/{temp.U_NAME}?start=file_{message.chat.id}_{f['_id']}>[{get_size(f['file_size'])}] {f.get('caption', formate_file_name(f['file_name']))}</a></b>"
            for i, f in enumerate(files, 1)
        ])
        btn = []
    else:
        links = ""
        btn = [[
            InlineKeyboardButton(
                f"🔗 {get_size(f['file_size'])}≽ {f.get('caption', formate_file_name(f['file_name']))}",
                url=f"https://telegram.dog/{temp.U_NAME}?start=file_{message.chat.id}_{f['_id']}"
            )
        ] for f in files]

    batch_link = f"batchfiles#{message.chat.id}#{message.id}#{message.from_user.id}"

    if offset and total_results >= int(MAX_BTN):
        # Multiple pages available
        btn.insert(0, [InlineKeyboardButton("• ʟᴀɴɢᴜᴀɢᴇ •", callback_data=f"languages#{key}#{offset}#{req}")])
        btn.insert(1, [
            InlineKeyboardButton("• ǫᴜᴀʟɪᴛʏ •", callback_data=f"qualities#{key}#{offset}#{req}"),
            InlineKeyboardButton("• sᴇᴀsᴏɴ •", callback_data=f"seasons#{key}#{offset}#{req}")
        ])
        btn.insert(2, [InlineKeyboardButton("• sᴇɴᴅ ᴀʟʟ •", callback_data=batch_link)])
        BUTTONS[key] = search
        total_pages = math.ceil(total_results / int(MAX_BTN))
        btn.append([
            InlineKeyboardButton(f"1/{total_pages}", callback_data="pages"),
            InlineKeyboardButton("ɴᴇxᴛ ⪼", callback_data=f"next_{req}_{key}_{offset}")
        ])
    else:

        btn.insert(0, [InlineKeyboardButton("• sᴇɴᴅ ᴀʟʟ •", callback_data=batch_link)])
        if not offset:
            btn.insert(1, [InlineKeyboardButton("ɴᴏ ᴍᴏʀᴇ ᴘᴀɢᴇs", user_id=ADMINS[0])])

    if spoll:
        m = await msg.message.edit(f"<b><code>{search}</code> ɪs ꜰᴏᴜɴᴅ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ ꜰᴏʀ ꜰɪʟᴇs 📫</b>")
        await asyncio.sleep(1.2)
        await m.delete()

    imdb = await get_poster(search, file=files[0]['file_name']) if settings.get("imdb") else None

    # Build caption
    if imdb:
        cap = settings['template'].format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"<b>📂 ʜᴇʀᴇ ɪ ꜰᴏᴜɴᴅ ꜰᴏʀ ʏᴏᴜʀ sᴇᴀʀᴄʜ {search}</b>"

    CAP[key] = cap

    async def send_response(photo_url=None):
        try:
            if photo_url:
                return await message.reply_photo(
                    photo=photo_url, 
                    caption=cap[:1024] + links + del_msg,
                    parse_mode=enums.ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(btn)
                )
            else:
                return await message.reply_text(
                    cap + links + del_msg,
                    parse_mode=enums.ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(btn),
                    disable_web_page_preview=True,
                    reply_to_message_id=message.id
                )
        except Exception as e:
            print(f"Send error: {e}")
            return await message.reply_text(
                cap + links + del_msg,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(btn),
                disable_web_page_preview=True
            )

    async def handle_auto_delete(response_msg):
        if settings.get("auto_delete"):
            await asyncio.sleep(DELETE_TIME)
            try:
                await response_msg.delete()
            except:
                pass

    if imdb and imdb.get('poster'):
        try:
            k = await send_response(imdb['poster'])
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            poster = imdb['poster'].replace('.jpg', "._V1_UX360.jpg")
            try:
                k = await send_response(poster)
            except:
                k = await send_response()
        except:
            k = await send_response()
    else:
        k = await send_response()

    if k and settings.get("auto_delete"):
        asyncio.create_task(handle_auto_delete(k))

async def silicon_spell_check(message):
    mv_id = message.id
    search = message.text
    chat_id = message.chat.id
    settings = await get_settings(chat_id)
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", message.text, flags=re.IGNORECASE)
    query = query.strip() + " movie"
    try:
        movies = await get_poster(search, bulk=True)
    except:
        k = await message.reply(script.I_CUDNT.format(message.from_user.mention))
        await asyncio.sleep(60)
      #  try:
      #      await message.delete()
      #  except:
      #      pass
        return
    if not movies:
        google = search.replace(" ", "+")
        button = [[
            InlineKeyboardButton("🔍 ᴄʜᴇᴄᴋ sᴘᴇʟʟɪɴɢ ᴏɴ ɢᴏᴏɢʟᴇ 🔍", url=f"https://www.google.com/search?q={google}")
        ],[
            InlineKeyboardButton("📮 ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴀᴅᴍɪɴ 📮", callback_data=f"req_admin#{search}#{message.from_user.id}")
        ]]
        k = await message.reply_text(text=script.I_CUDNT.format(search), reply_markup=InlineKeyboardMarkup(button))
        await asyncio.sleep(120)
        await k.delete()
       # try:
       #     await message.delete()
       # except:
       #     pass
        return
    user = message.from_user.id if message.from_user else 0
    buttons = [[
        InlineKeyboardButton(text=movie.get('title'), callback_data=f"spol#{movie.movieID}#{user}")
    ]
        for movie in movies
    ]
    buttons.append(
        [InlineKeyboardButton(text="🚫 ᴄʟᴏsᴇ 🚫", callback_data='close_data')]
    )
    d = await message.reply_text(text=script.CUDNT_FND.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(buttons), reply_to_message_id=message.id)
    await asyncio.sleep(120)
    await d.delete()
    #try:
      #  await message.delete()
  #  except:
     #   pass

@Client.on_callback_query(filters.regex(r"^req_admin"))
async def request_to_admin(bot, query):
    _, search, user_id = query.data.split('#')
    if int(user_id) != query.from_user.id:
        return await query.answer(script.ALRT_TXT, show_alert=True)
    
    # Create buttons similar to /request command
    buttons = [[
        InlineKeyboardButton('👀 View Request', url=f"{query.message.link}")
    ],[
        InlineKeyboardButton('⚙ Show Options', callback_data=f'show_options#{query.from_user.id}#{query.message.id}')
    ]]
    
    # Send to request channel (same as /request command)
    sent_request = await bot.send_message(
        REQUEST_CHANNEL,
        script.REQUEST_TXT.format(query.from_user.mention, query.from_user.id, search),
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
    # Send confirmation to user
    btn = [[
        InlineKeyboardButton('✨ ᴠɪᴇᴡ ʏᴏᴜʀ ʀᴇᴏ̨ᴜᴇsᴛ ✨', url=f"{sent_request.link}")
    ]]
    await query.message.edit_text(
        text="<b>✅ Your request has been sent to admin!</b>",
        reply_markup=InlineKeyboardMarkup(btn)
    )
    await query.answer()
