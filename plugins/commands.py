import os, requests
import logging
import random
import asyncio
import string
import pytz
from datetime import datetime, timedelta
from Script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup , ForceReply, ReplyKeyboardMarkup 
from database.users_chats_db import db
from database.extra_db import silicondb
from database.ia_filterdb import get_file_details
from utils import formate_file_name,  get_settings, save_group_settings, is_subscribed, is_req_subscribed, get_size, get_shortlink, is_check_admin, get_status, temp, get_readable_time, generate_trend_list, extract_limit_from_command, create_keyboard_layout, process_trending_data, log_error, group_setting_buttons
from .pm_filter import auto_filter
import re
import base64
from info import *

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client: Client, message): 
    m = message
    user_id = m.from_user.id

    try:
        data = message.command[1]
    except IndexError:
        data = None

    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(
            LOG_CHANNEL,
            script.NEW_USER_TXT.format(
                temp.B_LINK,
                message.from_user.id,
                message.from_user.mention
            )
        )

    def get_main_buttons():
        return [
            [InlineKeyboardButton('⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs ⇆', url=f'http://t.me/{temp.U_NAME}?startgroup=start')],
            [
                InlineKeyboardButton('• ꜰᴇᴀᴛᴜʀᴇs', callback_data='features'),
                InlineKeyboardButton('• ᴜᴘɢʀᴀᴅᴇ', callback_data='premium')
            ],
            [
                InlineKeyboardButton('• ᴛᴏᴘ', callback_data='top_search'),
                InlineKeyboardButton('• ᴀʙᴏᴜᴛ', callback_data='about')
            ],
            [InlineKeyboardButton('• ᴇᴀʀɴ ᴍᴏɴᴇʏ ᴡɪᴛʜ ʙᴏᴛ •', callback_data='earn')]
        ]

    if len(message.command) == 2 and data.startswith('getfile'):
        movies = message.command[1].split("-", 1)[1] 
        movie = movies.replace('-',' ')
        message.text = movie 
        await auto_filter(client, message) 
        return

    if data and data.startswith('notcopy'):
        _, userid, verify_id, file_id = data.split("_", 3)
        user_id = int(userid)
        grp_id = temp.CHAT.get(user_id, 0)
        settings = await get_settings(grp_id)         
        verify_id_info = await db.get_verify_id_info(user_id, verify_id)
        
        if not verify_id_info or verify_id_info["verified"]:
            await message.reply("<b>ʟɪɴᴋ ᴇxᴘɪʀᴇᴅ ᴛʀʏ ᴀɢᴀɪɴ...</b>")
            return  
            
        ist_timezone = pytz.timezone('Asia/Kolkata')
        key = "third_time_verified" if await db.user_verified(user_id) else ("second_time_verified" if await db.is_user_verified(user_id) else "last_verified")
        current_time = datetime.now(tz=ist_timezone)
        
        await db.update_notcopy_user(user_id, {key: current_time})
        await db.update_verify_id_info(user_id, verify_id, {"verified": True})
        
        num = 3 if key == "third_time_verified" else (2 if key == "second_time_verified" else 1)
        msg = script.THIRDT_VERIFY_COMPLETE_TEXT if key == "third_time_verified" else (script.SECOND_VERIFY_COMPLETE_TEXT if key == "second_time_verified" else script.VERIFY_COMPLETE_TEXT)
        
        await client.send_message(settings['log'], script.VERIFIED_LOG_TEXT.format(m.from_user.mention, user_id, datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d %B %Y'), num))
        
        btn = [[InlineKeyboardButton("‼️ ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ɢᴇᴛ ꜰɪʟᴇ ‼️", url=f"https://telegram.me/{temp.U_NAME}?start=file_{grp_id}_{file_id}")]]
        await m.reply_photo(
            photo=VERIFY_IMG,
            caption=msg.format(message.from_user.mention, get_readable_time(TWO_VERIFY_GAP)),
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.HTML
        )
        return

    if data and data.startswith("reff_"):
        try:
            user_id = int(message.command[1].split("_")[1])
        except ValueError:
            await message.reply_text("Invalid refer!")
            return
        if user_id == message.from_user.id:
            await message.reply_text("Hᴇʏ Dᴜᴅᴇ, Yᴏᴜ Cᴀɴ'ᴛ Rᴇғᴇʀ Yᴏᴜʀsᴇʟғ 🤣!\n\nsʜᴀʀᴇ ʟɪɴᴋ ʏᴏᴜʀ ғʀɪᴇɴᴅ ᴀɴᴅ ɢᴇᴛ 10 ʀᴇғᴇʀʀᴀʟ ᴘᴏɪɴᴛ ɪғ ʏᴏᴜ ᴀʀᴇ ᴄᴏʟʟᴇᴄᴛɪɴɢ 100 ʀᴇғᴇʀʀᴀʟ ᴘᴏɪɴᴛs ᴛʜᴇɴ ʏᴏᴜ ᴄᴀɴ ɢᴇᴛ 1 ᴍᴏɴᴛʜ ғʀᴇᴇ ᴘʀᴇᴍɪᴜᴍ ᴍᴇᴍʙᴇʀsʜɪᴘ.")
            return
        if silicondb.is_silicon_user_in_list(message.from_user.id):
            await message.reply_text("Yᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ᴀʟʀᴇᴀᴅʏ ɪɴᴠɪᴛᴇᴅ ❗")
            return
        if await db.is_user_exist(message.from_user.id): 
            await message.reply_text("‼️ Yᴏᴜ Hᴀᴠᴇ Bᴇᴇɴ Aʟʀᴇᴀᴅʏ Iɴᴠɪᴛᴇᴅ ᴏʀ Jᴏɪɴᴇᴅ")
            return
        try:
            uss = await client.get_users(user_id)
        except Exception:
            return 	    
        silicondb.add_user(message.from_user.id)
        fromuse = silicondb.get_silicon_refer_points(user_id) + 10
        if fromuse == 100:
            silicondb.add_refer_points(user_id, 0) 
            await message.reply_text(f"🎉 𝗖𝗼𝗻𝗴𝗿𝗮𝘁𝘂𝗹𝗮𝘁𝗶𝗼𝗻𝘀! 𝗬𝗼𝘂 𝘄𝗼𝗻 𝟭𝟬 𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹 𝗽𝗼𝗶𝗻𝘁 𝗯𝗲𝗰𝗮𝘂𝘀𝗲 𝗬𝗼𝘂 𝗵𝗮𝘃𝗲 𝗯𝗲𝗲𝗻 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗜𝗻𝘃𝗶𝘁𝗲𝗱 ☞ {uss.mention}!")		    
            await message.reply_text(user_id, f"You have been successfully invited by {message.from_user.mention}!") 	
            seconds = 2592000
            if seconds > 0:
                expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
                user_data = {"id": user_id, "expiry_time": expiry_time}
                await db.update_user(user_data)		    
                await client.send_message(
                chat_id=user_id,
                text=f"<b>Hᴇʏ {uss.mention}\n\nYᴏᴜ ɢᴏᴛ 1 ᴍᴏɴᴛʜ ᴘʀᴇᴍɪᴜᴍ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ʙʏ ɪɴᴠɪᴛɪɴɢ 10 ᴜsᴇʀs ❗", disable_web_page_preview=True              
                )
            for admin in ADMINS:
                await client.send_message(chat_id=admin, text=f"Sᴜᴄᴄᴇss ғᴜʟʟʏ ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ʙʏ ᴛʜɪs ᴜsᴇʀ:\n\nuser Nᴀᴍᴇ: {uss.mention}\n\nUsᴇʀ ɪᴅ: {uss.id}!")	
        else:
            silicondb.add_refer_points(user_id, fromuse)
            await message.reply_text(f"You have been successfully invited by {uss.mention}!")
            await client.send_message(user_id, f"𝗖𝗼𝗻𝗴𝗿𝗮𝘁𝘂𝗹𝗮𝘁𝗶𝗼𝗻𝘀! 𝗬𝗼𝘂 𝘄𝗼𝗻 𝟭𝟬 𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹 𝗽𝗼𝗶𝗻𝘁 𝗯𝗲𝗰𝗮𝘂𝘀𝗲 𝗬𝗼𝘂 𝗵𝗮𝘃𝗲 𝗯𝗲𝗲𝗻 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗜𝗻𝘃𝗶𝘁𝗲𝗱 ☞{message.from_user.mention}!")
        return

    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        status = get_status()
        sili = await message.reply_text(f"<b>🔥 ʏᴇs {status},\nʜᴏᴡ ᴄᴀɴ ɪ ʜᴇʟᴘ ʏᴏᴜ??</b>")
        await asyncio.sleep(600)
        await sili.delete()
        await m.delete()
        
        if str(message.chat.id).startswith("-100") and not await db.get_chat(message.chat.id):
            total = await client.get_chat_members_count(message.chat.id)
            group_link = await message.chat.export_invite_link()
            user = message.from_user.mention if message.from_user else "Dear" 
            await client.send_message(LOG_CHANNEL, script.NEW_GROUP_TXT.format(temp.B_LINK, message.chat.title, message.chat.id, message.chat.username, group_link, total, user))       
            await db.add_chat(message.chat.id, message.chat.title)
        return 

    if not data or data in ["subscribe", "error", "okay", "help"]:
        await message.reply_photo(
            photo=START_IMG,
            caption=script.START_TXT.format(message.from_user.mention, get_status(), message.from_user.id),
            reply_markup=InlineKeyboardMarkup(get_main_buttons()),
            parse_mode=enums.ParseMode.HTML
        )
        return
        
    try:
        pre, grp_id, file_id = data.split('_', 2)
    except ValueError:
        pre, grp_id, file_id = "", 0, data
        
    if not await db.has_premium_access(message.from_user.id):
        try:
            btn = []
            chat_id_str = data.split("_", 2)[1]
            try:
                chat = int(chat_id_str.split("-", 1)[0]) 
            except ValueError:
                chat = chat_id_str  

            settings = await get_settings(chat)
            fsub_channels = list(dict.fromkeys((settings.get('fsub', []) if settings else []) + AUTH_CHANNELS))

            if fsub_channels:
                btn += await is_subscribed(client, message.from_user.id, fsub_channels)
            if AUTH_REQ_CHANNELS:
                btn += await is_req_subscribed(client, message.from_user.id, AUTH_REQ_CHANNELS)
            if btn:
                if len(message.command) > 1 and "_" in message.command[1]:
                    parts = message.command[1].split("_", 1)
                    if len(parts) == 2:
                        kk, file_id = parts
                    else:
                        kk, file_id = message.command[1], ""
                    btn.append([
                        InlineKeyboardButton("♻️ ᴛʀʏ ᴀɢᴀɪɴ ♻️", callback_data=f"checksub#{kk}#{file_id}")
                    ])
                reply_markup = InlineKeyboardMarkup(btn)
                photo = random.choice(FSUB_PICS) if FSUB_PICS else "https://graph.org/file/7478ff3eac37f4329c3d8.jpg"
                caption = (
                    f"👋 ʜᴇʟʟᴏ {message.from_user.mention}\n\n"
                    "🛑 ʏᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴛʜᴇ ʀᴇǫᴜɪʀᴇᴅ ᴄʜᴀɴɴᴇʟs ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ.\n"
                    "👉 ᴊᴏɪɴ ᴀʟʟ ᴛʜᴇ ʙᴇʟᴏᴡ ᴄʜᴀɴɴᴇʟs ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ."
                )
                await message.reply_photo(
                    photo=photo,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode=enums.ParseMode.HTML
                )
                return

        except Exception as e:
            await log_error(client, f"❗️ Force Sub Error:\n\n{repr(e)}")
            logger.error(f"❗️ Force Sub Error:\n\n{repr(e)}")

    if not await db.has_premium_access(user_id):
        grp_id = int(grp_id)
        user_verified = await db.is_user_verified(user_id)
        settings = await get_settings(grp_id)
        is_second_shortener = await db.use_second_shortener(user_id, settings.get('verify_time', TWO_VERIFY_GAP)) 
        is_third_shortener = await db.use_third_shortener(user_id, settings.get('third_verify_time', THREE_VERIFY_GAP))

        is_allfiles_request = data and data.startswith("allfiles")

        if not is_allfiles_request and IS_FILE_LIMIT and FILES_LIMIT > 0:
            current_file_count = silicondb.silicon_file_limit(user_id)

            if current_file_count < FILES_LIMIT:
                silicondb.increment_silicon_limit(user_id)
                current_file_count += 1
                
                if not data:
                    return

                files_ = await get_file_details(file_id)           

                if not files_:
                    try:
                        pre, file_id = (base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii").split("_", 1)
                    except:
                        pass
                    return await message.reply('<b>⚠️ ᴀʟʟ ꜰɪʟᴇs ɴᴏᴛ ꜰᴏᴜɴᴅ ⚠️</b>')

                if isinstance(files_, list) and len(files_) > 0:
                    files = files_[0]
                elif isinstance(files_, dict):
                    files = files_
                else:
                    return await message.reply('<b>⚠️ ᴀʟʟ ꜰɪʟᴇs ɴᴏᴛ ꜰᴏᴜɴᴅ ⚠️</b>')

                settings = await get_settings(grp_id)

                file_limit_info = f"\n\n📊 ʏᴏᴜ ʜᴀᴠᴇ ʀᴇᴄᴇɪᴠᴇᴅ {current_file_count}/{FILES_LIMIT} ꜰʀᴇᴇ ꜰɪʟᴇs"
                
                f_caption = settings['caption'].format(
                    file_name=formate_file_name(files['file_name']),
                    file_size=get_size(files['file_size']),
                    file_caption=files.get('caption', '')
                ) + file_limit_info

                btn = [[InlineKeyboardButton("✛ ᴡᴀᴛᴄʜ & ᴅᴏᴡɴʟᴏᴀᴅ ✛", callback_data=f'stream#{file_id}')]]
                toDel = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    reply_markup=InlineKeyboardMarkup(btn)
                )

                time_text = f'{FILE_AUTO_DEL_TIMER / 60} ᴍɪɴᴜᴛᴇs' if FILE_AUTO_DEL_TIMER >= 60 else f'{FILE_AUTO_DEL_TIMER} sᴇᴄᴏɴᴅs'
                delCap = f"<b>ʏᴏᴜʀ ғɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ᴀғᴛᴇʀ {time_text} ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ᴠɪᴏʟᴀᴛɪᴏɴs!</b>"
                afterDelCap = f"<b>ʏᴏᴜʀ ғɪʟᴇ ɪs ᴅᴇʟᴇᴛᴇᴅ ᴀғᴛᴇʀ {time_text} ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ᴠɪᴏʟᴀᴛɪᴏɴs!</b>"

                replyed = await message.reply(delCap, reply_to_message_id=toDel.id)
                await asyncio.sleep(FILE_AUTO_DEL_TIMER)
                await toDel.delete()
                return await replyed.edit(afterDelCap)

        if settings.get("is_verify", IS_VERIFY) and (not user_verified or is_second_shortener or is_third_shortener):
            verify_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
            await db.create_verify_id(user_id, verify_id)
            temp.CHAT[user_id] = grp_id
            verify = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=notcopy_{user_id}_{verify_id}_{file_id}", grp_id, is_second_shortener, is_third_shortener)
            if is_third_shortener:
                silicon = settings.get('tutorial_three', TUTORIAL3)
            else:
                silicon = settings.get('tutorial_two', TUTORIAL2) if is_second_shortener else settings.get('tutorial', TUTORIAL)

            buttons = [
                [InlineKeyboardButton(text="♻️ ᴠᴇʀɪғʏ ♻️", url=verify)],
                [InlineKeyboardButton(text="❗️ ʜᴏᴡ ᴛᴏ ᴠᴇʀɪғʏ ❓", url=silicon)]
            ]

            msg = script.THIRDT_VERIFICATION_TEXT if await db.user_verified(user_id) else (script.SECOND_VERIFICATION_TEXT if is_second_shortener else script.VERIFICATION_TEXT)

            d = await m.reply_text(
                text=msg.format(message.from_user.mention, get_status()),
                protect_content=False,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=enums.ParseMode.HTML
            )
            await asyncio.sleep(300) 
            await d.delete()
            await m.delete()
            return

    if data and data.startswith("allfiles"):
        _, key = data.split("_", 1)
        files = temp.FILES_ID.get(key)
        if not files:
            await message.reply_text("<b>⚠️ ᴀʟʟ ꜰɪʟᴇs ɴᴏᴛ ꜰᴏᴜɴᴅ ⚠️</b>")
            return

        files_to_delete = []
        for file in files:
            grp_id = temp.CHAT.get(user_id)
            settings = await get_settings(grp_id)
            
            f_caption = settings['caption'].format(
                file_name=formate_file_name(file['file_name']),
                file_size=get_size(file['file_size']),
                file_caption=file.get('caption', '')
            )
            
            btn = [[InlineKeyboardButton("✛ ᴡᴀᴛᴄʜ & ᴅᴏᴡɴʟᴏᴀᴅ ✛", callback_data=f'stream#{file["_id"]}')]]
            toDel = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file['_id'],
                caption=f_caption,
                reply_markup=InlineKeyboardMarkup(btn)
             )
            files_to_delete.append(toDel)

        time_text = f'{FILE_AUTO_DEL_TIMER / 60} ᴍɪɴᴜᴛᴇs' if FILE_AUTO_DEL_TIMER >= 60 else f'{FILE_AUTO_DEL_TIMER} sᴇᴄᴏɴᴅs'
        delCap = f"<b>ᴀʟʟ {len(files_to_delete)} ғɪʟᴇs ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ᴀғᴛᴇʀ {time_text} ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ᴠɪᴏʟᴀᴛɪᴏɴs!</b>"
        afterDelCap = f"<b>ᴀʟʟ {len(files_to_delete)} ғɪʟᴇs ᴀʀᴇ ᴅᴇʟᴇᴛᴇᴅ ᴀғᴛᴇʀ {time_text} ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ᴠɪᴏʟᴀᴛɪᴏɴs!</b>"

        replyed = await message.reply(delCap)
        await asyncio.sleep(FILE_AUTO_DEL_TIMER)

        for file in files_to_delete:
            try:
                await file.delete()
            except:
                pass
        return await replyed.edit(afterDelCap)

    if not data:
        return

    files_ = await get_file_details(file_id)           

    if not files_:
        try:
            pre, file_id = (base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii").split("_", 1)
        except:
            pass
        return await message.reply('<b>⚠️ ᴀʟʟ ꜰɪʟᴇs ɴᴏᴛ ꜰᴏᴜɴᴅ ⚠️</b>')

    if isinstance(files_, list) and len(files_) > 0:
        files = files_[0]
    elif isinstance(files_, dict):
        files = files_
    else:
        return await message.reply('<b>⚠️ ᴀʟʟ ꜰɪʟᴇs ɴᴏᴛ ꜰᴏᴜɴᴅ ⚠️</b>')

    settings = await get_settings(grp_id)
    f_caption = settings['caption'].format(
        file_name=formate_file_name(files['file_name']),
        file_size=get_size(files['file_size']),
        file_caption=files.get('caption', '')
    )

    btn = [[InlineKeyboardButton("✛ ᴡᴀᴛᴄʜ & ᴅᴏᴡɴʟᴏᴀᴅ ✛", callback_data=f'stream#{file_id}')]]
    toDel = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        reply_markup=InlineKeyboardMarkup(btn)
    )

    time_text = f'{FILE_AUTO_DEL_TIMER / 60} ᴍɪɴᴜᴛᴇs' if FILE_AUTO_DEL_TIMER >= 60 else f'{FILE_AUTO_DEL_TIMER} sᴇᴄᴏɴᴅs'
    delCap = f"<b>ʏᴏᴜʀ ғɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ᴀғᴛᴇʀ {time_text} ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ᴠɪᴏʟᴀᴛɪᴏɴs!</b>"
    afterDelCap = f"<b>ʏᴏᴜʀ ғɪʟᴇ ɪs ᴅᴇʟᴇᴛᴇᴅ ᴀғᴛᴇʀ {time_text} ᴛᴏ ᴀᴠᴏɪᴅ ᴄᴏᴘʏʀɪɢʜᴛ ᴠɪᴏʟᴀᴛɪᴏɴs!</b>"

    replyed = await message.reply(delCap, reply_to_message_id=toDel.id)
    await asyncio.sleep(FILE_AUTO_DEL_TIMER)
    await toDel.delete()
    return await replyed.edit(afterDelCap)


@Client.on_message(filters.command("invite") & filters.private & filters.user(ADMINS))
async def invite(client, message):
    toGenInvLink = message.command[1]
    if len(toGenInvLink) != 14:
        return await message.reply("Invalid chat id\nAdd -100 before chat id if You did not add any yet.") 
    try:
        link = await client.export_chat_invite_link(toGenInvLink)
        await message.reply(link)
    except Exception as e:
        print(f'Error while generating invite link : {e}\nFor chat:{toGenInvLink}')
        await message.reply(f'Error while generating invite link : {e}\nFor chat:{toGenInvLink}')

@Client.on_message(filters.command('top_search'))
async def top(_, message):

    limit = extract_limit_from_command(message.command, default=20)
    
    searches = await process_trending_data(limit=limit, format_type="keyboard")
    keyboard = create_keyboard_layout(searches)
    
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True, placeholder="Most searches of the day")
    await message.reply_text(f"<b>Tᴏᴘ Sᴇᴀʀᴄʜᴇs Oғ Tʜᴇ Dᴀʏ 👇</b>", reply_markup=reply_markup)

@Client.on_message(filters.command('trendlist'))
async def trendlist(client, message):
    limit = extract_limit_from_command(message.command, default=31)
    if limit == -1:  
        return await message.reply_text("ɪɴᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ ғᴏʀᴍᴀᴛ.\nᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ ᴀғᴛᴇʀ ᴛʜᴇ /ᴛʀᴇɴᴅʟɪsᴛ ᴄᴏᴍᴍᴀɴᴅ.")
    
    try:
        searches = await process_trending_data(limit=limit, format_type="list")
        if not searches:
            return await message.reply_text("ɴᴏ ᴛʀᴇɴᴅɪɴɢ sᴇᴀʀᴄʜᴇs ғᴏᴜɴᴅ.")
        
        trend_list = generate_trend_list(searches)
        footer_msg = "⚡️ 𝑨𝒍𝒍 𝒕𝒉𝒆 𝒓𝒆𝒔𝒖𝒍𝒕𝒔 𝒂𝒃𝒐𝒗𝒆 𝒄𝒐𝒎𝒆 𝒇𝒓𝒐𝒎 𝒘𝒉𝒂𝒕 𝒖𝒔𝒆𝒓𝒔 𝒉𝒂𝒗𝒆 𝒔𝒆𝒂𝒓𝒄𝒉𝒆𝒅 𝒇𝒐𝒓. 𝑻𝒉𝒆𝒚'𝒓𝒆 𝒔𝒉𝒐𝒘𝒏 𝒕𝒐 𝒚𝒐𝒖 𝒆𝒙𝒂𝒄𝒕𝒍𝒚 𝒂𝒔 𝒕𝒉𝒆𝒚 𝒘𝒆𝒓𝒆 𝒔𝒆𝒂𝒓𝒄𝒉𝒆𝒅, 𝒘𝒊𝒕𝒉𝒐𝒖𝒕 𝒂𝒏𝒚 𝒄𝒉𝒂𝒏𝒈𝒆𝒔 𝒃𝒚 𝒕𝒉𝒆 𝒐𝒘𝒏𝒆𝒓."
        
        final_text = f"<b>ᴛᴏᴘ {len(searches)} ᴛʀᴇɴᴅɪɴɢ ᴏғ ᴛʜᴇ ᴅᴀʏ 👇:</b>\n\n{trend_list}\n\n{footer_msg}"
        await message.reply_text(final_text)
        
    except Exception as e:
        await message.reply_text(f"Error retrieving trending data: {str(e)}")

@Client.on_message(filters.command('delete'))
async def delete_file(bot, message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.delete()
        return
    try:
        query = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ!\nᴜsᴀɢᴇ: /delete ǫᴜᴇʀʏ")
    btn = [[
        InlineKeyboardButton("ʏᴇs", callback_data=f"delete_{query}")
    ],[
        InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close_data")
    ]]
    await message.reply_text(f"ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴀʟʟ: {query} ?", reply_markup=InlineKeyboardMarkup(btn))

@Client.on_message(filters.command('deleteall'))
async def delete_all_index(bot, message):

    btn = [[
            InlineKeyboardButton(text="ʏᴇs", callback_data="all_files_delete")
        ],[
            InlineKeyboardButton(text="ᴄᴀɴᴄᴇʟ", callback_data="close_data")
        ]]
    if message.from_user.id not in ADMINS:
        await message.reply('ᴏɴʟʏ ᴛʜᴇ ʙᴏᴛ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ... 😑')
        return
    await message.reply_text('<b>ᴛʜɪs ᴡɪʟʟ ᴅᴇʟᴇᴛᴇ ᴀʟʟ ɪɴᴅᴇxᴇᴅ ꜰɪʟᴇs.\nᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ??</b>', reply_markup=InlineKeyboardMarkup(btn))

@Client.on_message(filters.command('settings'))
async def settings(client, message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return await message.reply("<b>💔 ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ...</b>")
    chat_type = message.chat.type
    if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        if not await is_check_admin(client, grp_id, message.from_user.id):
            return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
        await db.connect_group(grp_id, user_id)
        settings = await get_settings(grp_id)
        title = message.chat.title
        if settings is not None:
                btn = await group_setting_buttons(int(grp_id))
                await message.reply_text(
                    text=(
                        f"ᴄʜᴀɴɢᴇ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ꜰᴏʀ <b> {title} ⚙ </b>\n"
                        f"ɢʀᴏᴜᴘ ɪᴅ - <code>{grp_id}</code> ✨"
                    ),
                    reply_markup=InlineKeyboardMarkup(btn),
                    parse_mode=enums.ParseMode.HTML
                )
    elif chat_type == enums.ChatType.PRIVATE:
        connected_groups = await db.get_connected_grps(user_id)
        if not connected_groups:
            return await message.reply_text("No Connected Groups Found .")
        list = []
        for group in connected_groups:
            try:
                gt = await client.get_chat(int(group))
                list.append([
                    InlineKeyboardButton(text=gt.title, callback_data=f"group_pm#{gt.id}")
                ])
            except Exception as e:
                print(f"⚠️ Removing inaccessible group {group}: {e}")
                await db.disconnect_group(int(group), user_id)
                continue
        if not list:
            return await message.reply_text("No Accessible Connected Groups Found.")
        await message.reply_text(
            'Here Is Your Connected Groups.',
            reply_markup=InlineKeyboardMarkup(list)
        )

@Client.on_message(filters.command('set_template'))
async def save_template(client, message):
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    try:
        template = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("Command Incomplete!")    
    await save_group_settings(grp_id, 'template', template)
    await message.reply_text(f"Successfully changed template for {title} to\n\n{template}", disable_web_page_preview=True)

@Client.on_message(filters.command("resetlimit") & filters.user(ADMINS))
async def reset_all_limits(client, message):
    try:
        silicondb.reset_all_file_limits()
        await message.reply_text(
            "<b>✅ sᴜᴄᴄᴇssꜰᴜʟʟʏ ʀᴇsᴇᴛ ꜰɪʟᴇ ʟɪᴍɪᴛs ꜰᴏʀ ᴀʟʟ ᴜsᴇʀs!</b>", 
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(
            f"<b>❌ Error resetting limits: {str(e)}</b>", 
            parse_mode=enums.ParseMode.HTML
        )

@Client.on_message(filters.command("resetuser") & filters.user(ADMINS))
async def reset_user_limit(client, message):
    try:
        if len(message.command) < 2:
            return await message.reply_text(
                "<b>❌ ᴜsᴀɢᴇ: /resetuser ᴜsᴇʀ_ɪᴅ</b>", 
                parse_mode=enums.ParseMode.HTML
            )
        
        user_id = int(message.command[1])
        old_limit = silicondb.silicon_file_limit(user_id)
        silicondb.reset_file_limit(user_id)
        
        await message.reply_text(
            f"<b>✅ sᴜᴄᴄᴇssꜰᴜʟʟʏ ʀᴇsᴇᴛ ꜰɪʟᴇ ʟɪᴍɪᴛ ꜰᴏʀ ᴜsᴇʀ {user_id}!\n\n"
            f"ᴘʀᴇᴠɪᴏᴜs ʟɪᴍɪᴛ: {old_limit}\n"
            f"ᴄᴜʀʀᴇɴᴛ ʟɪᴍɪᴛ: 0</b>", 
            parse_mode=enums.ParseMode.HTML
        )
        
    except ValueError:
        await message.reply_text(
            "<b>❌ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ!</b>", 
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(
            f"<b>❌ ᴇʀʀᴏʀ ʀᴇsᴇᴛᴛɪɴɢ ᴜsᴇʀ ʟɪᴍɪᴛ: {str(e)}</b>", 
            parse_mode=enums.ParseMode.HTML
        )

@Client.on_message(filters.command("checklimit") & filters.user(ADMINS))
async def check_user_limit(client, message):
    try:
        if len(message.command) < 2:
            return await message.reply_text(
                "<b>❌ ᴜsᴀɢᴇ: /checklimit ᴜsᴇʀ_ɪᴅ</b>", 
                parse_mode=enums.ParseMode.HTML
            )
        
        user_id = int(message.command[1])
        current_limit = silicondb.silicon_file_limit(user_id)
        
        await message.reply_text(
            f"<b>📊 ꜰɪʟᴇ ʟɪᴍɪᴛ sᴛᴀᴛᴜs ꜰᴏʀ ᴜsᴇʀ {user_id}:\n\n"
            f"ᴄᴜʀʀᴇɴᴛ ᴅᴏᴡɴʟᴏᴀᴅs: {current_limit}/{FILES_LIMIT}\n"
            f"ʀᴇᴍᴀɪɴɪɴɢ: {max(0, FILES_LIMIT - current_limit)}</b>", 
            parse_mode=enums.ParseMode.HTML
        )
        
    except ValueError:
        await message.reply_text(
            "<b>❌ ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ!</b>", 
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(
            f"<b>❌ ᴇʀʀᴏʀ ᴄʜᴇᴄᴋɪɴɢ ᴜsᴇʀ ʟɪᴍɪᴛ: {str(e)}</b>", 
            parse_mode=enums.ParseMode.HTML
        )
    
@Client.on_message(filters.command("send"))
async def send_msg(bot, message):
    if message.from_user.id not in ADMINS:
        await message.reply('<b>ᴏɴʟʏ ᴛʜᴇ ʙᴏᴛ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ...</b>')
        return
    if message.reply_to_message:
        target_ids = message.text.split(" ")[1:]
        if not target_ids:
            await message.reply_text("<b>ᴘʟᴇᴀꜱᴇ ᴘʀᴏᴠɪᴅᴇ ᴏɴᴇ ᴏʀ ᴍᴏʀᴇ ᴜꜱᴇʀ ɪᴅꜱ ᴀꜱ ᴀ ꜱᴘᴀᴄᴇ...</b>")
            return
        out = "\n\n"
        success_count = 0
        try:
            users = await db.get_all_users()
            for target_id in target_ids:
                try:
                    user = await bot.get_users(target_id)
                    out += f"{user.id}\n"
                    await message.reply_to_message.copy(int(user.id))
                    success_count += 1
                except Exception as e:
                    out += f"‼️ ᴇʀʀᴏʀ ɪɴ ᴛʜɪꜱ ɪᴅ - <code>{target_id}</code> <code>{str(e)}</code>\n"
            await message.reply_text(f"<b>✅️ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴍᴇꜱꜱᴀɢᴇ ꜱᴇɴᴛ ɪɴ `{success_count}` ɪᴅ\n<code>{out}</code></b>")
        except Exception as e:
            await message.reply_text(f"<b>‼️ ᴇʀʀᴏʀ - <code>{e}</code></b>")
    else:
        await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴀꜱ ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴍᴇꜱꜱᴀɢᴇ, ꜰᴏʀ ᴇɢ - <code>/send userid1 userid2</code></b>")

@Client.on_message(filters.regex(r"^(#request|/request|/Request|#Request|/req|#req|/Req|#Req)"))
async def send_request(bot, message):
    try:
        request = message.text.split(" ", 1)[1]
    except:
        await message.reply_text("<b>‼️ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ɪs ɪɴᴄᴏᴍᴘʟᴇᴛᴇ</b>")
        return
    buttons = [[
        InlineKeyboardButton('👀 ᴠɪᴇᴡ ʀᴇǫᴜᴇꜱᴛ 👀', url=f"{message.link}")
    ],[
        InlineKeyboardButton('⚙ sʜᴏᴡ ᴏᴘᴛɪᴏɴ ⚙', callback_data=f'show_options#{message.from_user.id}#{message.id}')
    ]]
    sent_request = await bot.send_message(REQUEST_CHANNEL, script.REQUEST_TXT.format(message.from_user.mention, message.from_user.id, request), reply_markup=InlineKeyboardMarkup(buttons))
    btn = [[
         InlineKeyboardButton('✨ ᴠɪᴇᴡ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ✨', url=f"{sent_request.link}")
    ]]
    await message.reply_text("<b>✅ sᴜᴄᴄᴇꜱꜱғᴜʟʟʏ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ᴀᴅᴅᴇᴅ, ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ ꜱᴏᴍᴇᴛɪᴍᴇ...</b>", reply_markup=InlineKeyboardMarkup(btn))


@Client.on_message(filters.command('set_caption'))
async def save_caption(client, message):
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    try:
        caption = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("Command Incomplete!")
    await save_group_settings(grp_id, 'caption', caption)
    await message.reply_text(f"Successfully changed caption for {title} to\n\n{caption}", disable_web_page_preview=True) 
    
@Client.on_message(filters.command("set_tutorial"))
async def tutorial(bot, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ.</b>")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        await message.reply_text("<b>ᴏɴʟʏ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ 😂</b>")
        return
    try:
        tutorial = re.search(r"https?://[^\s]+", message.text).group()
    except:
        return await message.reply_text("<b><u><i>ɪɴᴠᴀɪʟᴅ ꜰᴏʀᴍᴀᴛ!!</i></u>\n\nᴜsᴇ ʟɪᴋᴇ ᴛʜɪs - </b>\n<code>/sey_tutorial https://t.me/Silicon_Bot_Update</code>")
    reply = await message.reply_text("<b>ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
    await save_group_settings(grpid, 'tutorial', tutorial)
    await reply.edit_text(f"<b>sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴄʜᴀɴɢᴇᴅ ᴛᴜᴛᴏʀɪᴀʟ ꜰᴏʀ {title}</b>\n\nʟɪɴᴋ - {tutorial}", disable_web_page_preview=True)
    
@Client.on_message(filters.command("set_tutorial_2"))
async def tutorial_two(bot, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ.</b>")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        await message.reply_text("<b>ᴏɴʟʏ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ 😂</b>")
        return
    try:
        tutorial_two = re.search(r"https?://[^\s]+", message.text).group()
    except:
        return await message.reply_text("<b><u><i>ɪɴᴠᴀɪʟᴅ ꜰᴏʀᴍᴀᴛ!!</i></u>\n\nᴜsᴇ ʟɪᴋᴇ ᴛʜɪs - </b>\n<code>/set_tutorial_2 https://t.me/Silicon_Bot_Update</code>")
    reply = await message.reply_text("<b>ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
    await save_group_settings(grpid, 'tutorial_two', tutorial_two)
    await reply.edit_text(f"<b>sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴄʜᴀɴɢᴇᴅ 𝟸ɴᴅ ᴛᴜᴛᴏʀɪᴀʟ ꜰᴏʀ {title}</b>\n\nʟɪɴᴋ - {tutorial_two}", disable_web_page_preview=True)

@Client.on_message(filters.command("set_tutorial_3"))
async def tutorial_three(bot, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ.</b>")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        await message.reply_text("<b>ᴏɴʟʏ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ 😂</b>")
        return
    try:
        tutorial_three = re.search(r"https?://[^\s]+", message.text).group()
    except:
        return await message.reply_text("<b><u><i>ɪɴᴠᴀɪʟᴅ ꜰᴏʀᴍᴀᴛ!!</i></u>\n\nᴜsᴇ ʟɪᴋᴇ ᴛʜɪs - </b>\n<code>/set_tutorial_3 https://t.me/Silicon_Bot_Update</code>")
    reply = await message.reply_text("<b>ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
    await save_group_settings(grpid, 'tutorial_three', tutorial_three)
    await reply.edit_text(f"<b>sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴄʜᴀɴɢᴇᴅ 𝟹ʀᴅ ᴛᴜᴛᴏʀɪᴀʟ ꜰᴏʀ {title}</b>\n\nʟɪɴᴋ - {tutorial_three}", disable_web_page_preview=True)

@Client.on_message(filters.command('set_shortner'))
async def set_shortner(c, m):
    grp_id = m.chat.id
    chat_type = m.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await m.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    if not await is_check_admin(c, grp_id, m.from_user.id):
        return await m.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')        
    if len(m.text.split()) == 1:
        await m.reply("<b>Use this command like this - \n\n`/set_shortner tnshort.net 06b24eb6bbb025713cd522fb3f696b6d5de11354`</b>")
        return        
    sts = await m.reply("<b>♻️ ᴄʜᴇᴄᴋɪɴɢ...</b>")
    await asyncio.sleep(1.2)
    await sts.delete()
    try:
        URL = m.command[1]
        API = m.command[2]
        resp = requests.get(f'https://{URL}/api?api={API}&url=https://telegram.dog/bisal_files').json()
        if resp['status'] == 'success':
            SHORT_LINK = resp['shortenedUrl']
        await save_group_settings(grp_id, 'shortner', URL)
        await save_group_settings(grp_id, 'api', API)
        await m.reply_text(f"<b><u>✓ sᴜᴄᴄᴇssꜰᴜʟʟʏ ʏᴏᴜʀ sʜᴏʀᴛɴᴇʀ ɪs ᴀᴅᴅᴇᴅ</u>\n\nᴅᴇᴍᴏ - {SHORT_LINK}\n\nsɪᴛᴇ - `{URL}`\n\nᴀᴘɪ - `{API}`</b>", quote=True)
        user_id = m.from_user.id
        user_info = f"@{m.from_user.username}" if m.from_user.username else f"{m.from_user.mention}"
        link = (await c.get_chat(m.chat.id)).invite_link
        grp_link = f"[{m.chat.title}]({link})"
        log_message = f"#New_Shortner_Set_For_1st_Verify\n\nName - {user_info}\nId - `{user_id}`\n\nDomain name - {URL}\nApi - `{API}`\nGroup link - {grp_link}"
        await c.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)
    except Exception as e:
        await save_group_settings(grp_id, 'shortner', SHORTENER_WEBSITE)
        await save_group_settings(grp_id, 'api', SHORTENER_API)
        await m.reply_text(f"<b><u>💢 ᴇʀʀᴏʀ ᴏᴄᴄᴏᴜʀᴇᴅ!!</u>\n\nᴀᴜᴛᴏ ᴀᴅᴅᴇᴅ ʙᴏᴛ ᴏᴡɴᴇʀ ᴅᴇꜰᴜʟᴛ sʜᴏʀᴛɴᴇʀ\n\nɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄʜᴀɴɢᴇ ᴛʜᴇɴ ᴜsᴇ ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ ᴏʀ ᴀᴅᴅ ᴠᴀʟɪᴅ sʜᴏʀᴛʟɪɴᴋ ᴅᴏᴍᴀɪɴ ɴᴀᴍᴇ & ᴀᴘɪ\n\nʏᴏᴜ ᴄᴀɴ ᴀʟsᴏ ᴄᴏɴᴛᴀᴄᴛ ᴏᴜʀ <a href=https://t.me/Silicon_Botz>sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ</a> ꜰᴏʀ sᴏʟᴠᴇ ᴛʜɪs ɪssᴜᴇ...\n\nʟɪᴋᴇ -\n\n`/set_shortner mdiskshortner.link e7beb3c8f756dfa15d0bec495abc65f58c0dfa95`\n\n💔 ᴇʀʀᴏʀ - <code>{e}</code></b>", quote=True)

@Client.on_message(filters.command('set_shortner_2'))
async def set_shortner_2(c, m):
    grp_id = m.chat.id
    chat_type = m.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await m.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    if not await is_check_admin(c, grp_id, m.from_user.id):
        return await m.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    if len(m.text.split()) == 1:
        await m.reply("<b>Use this command like this - \n\n`/set_shortner_2 tnshort.net 06b24eb6bbb025713cd522fb3f696b6d5de11354`</b>")
        return
    sts = await m.reply("<b>♻️ ᴄʜᴇᴄᴋɪɴɢ...</b>")
    await asyncio.sleep(1.2)
    await sts.delete()
    try:
        URL = m.command[1]
        API = m.command[2]
        resp = requests.get(f'https://{URL}/api?api={API}&url=https://telegram.dog/bisal_files').json()
        if resp['status'] == 'success':
            SHORT_LINK = resp['shortenedUrl']
        await save_group_settings(grp_id, 'shortner_two', URL)
        await save_group_settings(grp_id, 'api_two', API)
        await m.reply_text(f"<b><u>✅ sᴜᴄᴄᴇssꜰᴜʟʟʏ ʏᴏᴜʀ sʜᴏʀᴛɴᴇʀ ɪs ᴀᴅᴅᴇᴅ</u>\n\nᴅᴇᴍᴏ - {SHORT_LINK}\n\nsɪᴛᴇ - `{URL}`\n\nᴀᴘɪ - `{API}`</b>", quote=True)
        user_id = m.from_user.id
        user_info = f"@{m.from_user.username}" if m.from_user.username else f"{m.from_user.mention}"
        link = (await c.get_chat(m.chat.id)).invite_link
        grp_link = f"[{m.chat.title}]({link})"
        log_message = f"#New_Shortner_Set_For_2nd_Verify\n\nName - {user_info}\nId - `{user_id}`\n\nDomain name - {URL}\nApi - `{API}`\nGroup link - {grp_link}"
        await c.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)
    except Exception as e:
        await save_group_settings(grp_id, 'shortner_two', SHORTENER_WEBSITE2)
        await save_group_settings(grp_id, 'api_two', SHORTENER_API2)
        await m.reply_text(f"<b><u>💢 ᴇʀʀᴏʀ ᴏᴄᴄᴏᴜʀᴇᴅ!!</u>\n\nᴀᴜᴛᴏ ᴀᴅᴅᴇᴅ ʙᴏᴛ ᴏᴡɴᴇʀ ᴅᴇꜰᴜʟᴛ sʜᴏʀᴛɴᴇʀ\n\nɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄʜᴀɴɢᴇ ᴛʜᴇɴ ᴜsᴇ ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ ᴏʀ ᴀᴅᴅ ᴠᴀʟɪᴅ sʜᴏʀᴛʟɪɴᴋ ᴅᴏᴍᴀɪɴ ɴᴀᴍᴇ & ᴀᴘɪ\n\nʏᴏᴜ ᴄᴀɴ ᴀʟsᴏ ᴄᴏɴᴛᴀᴄᴛ ᴏᴜʀ <a href=https://t.me/Silicon_Botz>sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ</a> ꜰᴏʀ sᴏʟᴠᴇ ᴛʜɪs ɪssᴜᴇ...\n\nʟɪᴋᴇ -\n\n`/set_shortner_2 mdiskshortner.link e7beb3c8f756dfa15d0bec495abc65f58c0dfa95`\n\n💔 ᴇʀʀᴏʀ - <code>{e}</code></b>", quote=True)

@Client.on_message(filters.command('set_shortner_3'))
async def set_shortner_3(c, m):
    chat_type = m.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await m.reply_text("<b>Use this command in Your group ! Not in Private</b>")
    if len(m.text.split()) == 1:
        return await m.reply("<b>Use this command like this - \n\n`/set_shortner_3 tnshort.net 06b24eb6bbb025713cd522fb3f696b6d5de11354`</b>")
    sts = await m.reply("<b>♻️ ᴄʜᴇᴄᴋɪɴɢ...</b>")
    await sts.delete()
    userid = m.from_user.id if m.from_user else None
    if not userid:
        return await m.reply(f"<b>⚠️ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ᴏꜰ ᴛʜɪs ɢʀᴏᴜᴘ</b>")
    grp_id = m.chat.id
    #check if user admin or not
    if not await is_check_admin(c, grp_id, userid):
        return await m.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    if len(m.command) == 1:
        await m.reply_text("<b>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴀᴅᴅ sʜᴏʀᴛɴᴇʀ & ᴀᴘɪ\n\nᴇx - `/set_shortner_3 mdiskshortner.link e7beb3c8f756dfa15d0bec495abc65f58c0dfa95`</b>", quote=True)
        return
    try:
        URL = m.command[1]
        API = m.command[2]
        resp = requests.get(f'https://{URL}/api?api={API}&url=https://telegram.dog/bisal_files').json()
        if resp['status'] == 'success':
            SHORT_LINK = resp['shortenedUrl']
        await save_group_settings(grp_id, 'shortner_three', URL)
        await save_group_settings(grp_id, 'api_three', API)
        await m.reply_text(f"<b><u>✅ sᴜᴄᴄᴇssꜰᴜʟʟʏ ʏᴏᴜʀ sʜᴏʀᴛɴᴇʀ ɪs ᴀᴅᴅᴇᴅ</u>\n\nᴅᴇᴍᴏ - {SHORT_LINK}\n\nsɪᴛᴇ - `{URL}`\n\nᴀᴘɪ - `{API}`</b>", quote=True)
        user_id = m.from_user.id
        if m.from_user.username:
            user_info = f"@{m.from_user.username}"
        else:
            user_info = f"{m.from_user.mention}"
        link = (await c.get_chat(m.chat.id)).invite_link
        grp_link = f"[{m.chat.title}]({link})"
        log_message = f"#New_Shortner_Set_For_3rd_Verify\n\nName - {user_info}\nId - `{user_id}`\n\nDomain name - {URL}\nApi - `{API}`\nGroup link - {grp_link}"
        await c.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)
    except Exception as e:
        await save_group_settings(grp_id, 'shortner_three', SHORTENER_WEBSITE3)
        await save_group_settings(grp_id, 'api_three', SHORTENER_API3)
        await m.reply_text(f"<b><u>💢 ᴇʀʀᴏʀ ᴏᴄᴄᴏᴜʀᴇᴅ!!</u>\n\nᴀᴜᴛᴏ ᴀᴅᴅᴇᴅ ʙᴏᴛ ᴏᴡɴᴇʀ ᴅᴇꜰᴜʟᴛ sʜᴏʀᴛɴᴇʀ\n\nɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄʜᴀɴɢᴇ ᴛʜᴇɴ ᴜsᴇ ᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ ᴏʀ ᴀᴅᴅ ᴠᴀʟɪᴅ sʜᴏʀᴛʟɪɴᴋ ᴅᴏᴍᴀɪɴ ɴᴀᴍᴇ & ᴀᴘɪ\n\nʏᴏᴜ ᴄᴀɴ ᴀʟsᴏ ᴄᴏɴᴛᴀᴄᴛ ᴏᴜʀ <a href=https://t.me/Silicon_Botz>sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ</a> ꜰᴏʀ sᴏʟᴠᴇ ᴛʜɪs ɪssᴜᴇ...\n\nʟɪᴋᴇ -\n\n`/set_shortner_3 mdiskshortner.link e7beb3c8f756dfa15d0bec495abc65f58c0dfa95`\n\n💔 ᴇʀʀᴏʀ - <code>{e}</code></b>", quote=True)

@Client.on_message(filters.command('set_time_2'))
async def set_time_2(client, message):
    userid = message.from_user.id if message.from_user else None
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")       
    if not userid:
        return await message.reply("<b>ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ...</b>")
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    try:
        time = int(message.text.split(" ", 1)[1])
    except:
        return await message.reply_text("Command Incomplete!")   
    await save_group_settings(grp_id, 'verify_time', time)
    await message.reply_text(f"Successfully set 1st verify time for {title}\n\nTime is - <code>{time}</code>")

@Client.on_message(filters.command('set_time_3'))
async def set_time_3(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply("<b>ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ...</b>")
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")       
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    try:
        time = int(message.text.split(" ", 1)[1])
    except:
        return await message.reply_text("ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ!")   
    await save_group_settings(grp_id, 'third_verify_time', time)
    await message.reply_text(f"sᴜᴄᴄᴇssғᴜʟʟʏ sᴇᴛ 𝟷sᴛ ᴠᴇʀɪғʏ ᴛɪᴍᴇ ғᴏʀ {title}\n\nᴛɪᴍᴇ ɪs - <code>{time}</code>")

@Client.on_message(filters.command('set_log_channel'))
async def set_log(client, message):
    grp_id = message.chat.id
    title = message.chat.title
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')
    if len(message.text.split()) == 1:
        await message.reply("<b>Use this command like this - \n\n`/set_log_channel -100******`</b>")
        return
    sts = await message.reply("<b>♻️ ᴄʜᴇᴄᴋɪɴɢ...</b>")
    await asyncio.sleep(1.2)
    await sts.delete()
    chat_type = message.chat.type
    try:
        log = int(message.text.split(" ", 1)[1])
    except IndexError:
        return await message.reply_text("<b><u>ɪɴᴠᴀɪʟᴅ ꜰᴏʀᴍᴀᴛ!!</u>\n\nᴜsᴇ ʟɪᴋᴇ ᴛʜɪs - `/set_log_channel -100xxxxxxxx`</b>")
    except ValueError:
        return await message.reply_text('<b>ᴍᴀᴋᴇ sᴜʀᴇ ɪᴅ ɪs ɪɴᴛᴇɢᴇʀ...</b>')
    try:
        t = await client.send_message(chat_id=log, text="<b>ʜᴇʏ ᴡʜᴀᴛ's ᴜᴘ!!</b>")
        await asyncio.sleep(3)
        await t.delete()
    except Exception as e:
        return await message.reply_text(f'<b><u>😐 ᴍᴀᴋᴇ sᴜʀᴇ ᴛʜɪs ʙᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ...</u>\n\n💔 ᴇʀʀᴏʀ - <code>{e}</code></b>')
    await save_group_settings(grp_id, 'log', log)
    await message.reply_text(f"<b>✅ sᴜᴄᴄᴇssꜰᴜʟʟʏ sᴇᴛ ʏᴏᴜʀ ʟᴏɢ ᴄʜᴀɴɴᴇʟ ꜰᴏʀ {title}\n\nɪᴅ - `{log}`</b>", disable_web_page_preview=True)
    user_id = message.from_user.id
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.mention}"
    link = (await client.get_chat(message.chat.id)).invite_link
    grp_link = f"[{message.chat.title}]({link})"
    log_message = f"#New_Log_Channel_Set\n\nName - {user_info}\nId - `{user_id}`\n\nLog channel id - `{log}`\nGroup link - {grp_link}"
    await client.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)  

@Client.on_message(filters.command('details'))
async def all_settings(client, message):
    grp_id = message.chat.id
    title = message.chat.title
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text('<b>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜɪꜱ ɢʀᴏᴜᴘ</b>')

    settings = await get_settings(grp_id)

    fsub_ids = settings.get("fsub", [])
    fsub_channels = ""
    if fsub_ids:
        for id in fsub_ids:
            try:
                chat = await client.get_chat(id)
                fsub_channels += f"📌 {chat.title} (`{id}`)\n"
            except Exception as e:
                fsub_channels += f"⚠️ Error fetching channel `{id}`: {e}\n"
    else:
        fsub_channels = "None set."

    text = f"""<b><u>⚙️ ʏᴏᴜʀ sᴇᴛᴛɪɴɢs ꜰᴏʀ -</u> {title}

<✅️ <b><u>1sᴛ ᴠᴇʀɪꜰʏ sʜᴏʀᴛɴᴇʀ</u></b>
<b>ɴᴀᴍᴇ</b> - <code>{settings["shortner"]}</code>
<b>ᴀᴘɪ</b> - <code>{settings["api"]}</code>

✅️ <b><u>2ɴᴅ ᴠᴇʀɪꜰʏ sʜᴏʀᴛɴᴇʀ</u></b>
<b>ɴᴀᴍᴇ</b> - <code>{settings["shortner_two"]}</code>
<b>ᴀᴘɪ</b> - <code>{settings["api_two"]}</code>

✅️ <b><u>𝟹ʀᴅ ᴠᴇʀɪꜰʏ sʜᴏʀᴛɴᴇʀ</u></b>
<b>ɴᴀᴍᴇ</b> - <code>{settings["shortner_three"]}</code>
<b>ᴀᴘɪ</b> - <code>{settings["api_three"]}</code>

⏰ <b>2ɴᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ</b> - <code>{settings["verify_time"]}</code>

⏰ <b>𝟹ʀᴅ ᴠᴇʀɪꜰɪᴄᴀᴛɪᴏɴ ᴛɪᴍᴇ</b> - <code>{settings['third_verify_time']}</code>

1️⃣ 1sᴛ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ - `{settings['tutorial']}`

2️⃣ 2ɴᴅ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ - `{settings['tutorial_two']}`

3️⃣ 3ʀᴅ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ - `{settings['tutorial_three']}`

📢 <u>ꜰ-sᴜʙ ᴄʜᴀɴɴᴇʟ(s):</u>
{fsub_channels}

📝 ʟᴏɢ ᴄʜᴀɴɴᴇʟ ɪᴅ - `{settings['log']}`

🎯 ɪᴍᴅʙ ᴛᴇᴍᴘʟᴀᴛᴇ - `{settings['template']}`

📂 ꜰɪʟᴇ ᴄᴀᴘᴛɪᴏɴ - `{settings['caption']}`</b>

<i>ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʀᴇsᴇᴛ ᴀʟʟ ᴅᴀᴛᴀ ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ʀᴇsᴇᴛ ᴅᴀᴛᴀ ʙᴜᴛᴛᴏɴ.<i>
"""

    btn = [[
        InlineKeyboardButton("ʀᴇꜱᴇᴛ ᴅᴀᴛᴀ", callback_data="reset_grp_data")
    ],[
        InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close_data")
    ]]
    reply_markup = InlineKeyboardMarkup(btn)
    dlt = await message.reply_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    await asyncio.sleep(300)
    await dlt.delete()

@Client.on_message(filters.command('auto_filter') & filters.user(ADMINS))
async def auto_filter_toggle(bot, message):
    if len(message.command) < 2:
        await message.reply('ᴜsᴀɢᴇ: /auto_filter on/off\n\nᴇxᴀᴍᴘʟᴇ: `/auto_filter on` ᴏʀ `/auto_filter off`')
        return
    
    action = message.command[1].lower()
    
    if action == 'on':
        silicondb.update_bot_sttgs('AUTO_FILTER', True)
        await message.reply('✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴛᴜʀɴᴇᴅ **ᴏɴ** ᴀᴜᴛᴏ ғɪʟᴛᴇʀ ғᴏʀ ᴀʟʟ ɢʀᴏᴜᴘs')
    elif action == 'off':
        silicondb.update_bot_sttgs('AUTO_FILTER', False)
        await message.reply('❌ sᴜᴄᴄᴇssғᴜʟʟʏ ᴛᴜʀɴᴇᴅ **ᴏғғ** ᴀᴜᴛᴏ ғɪʟᴛᴇʀ ғᴏʀ ᴀʟʟ ɢʀᴏᴜᴘs')
    else:
        await message.reply('❗ ɪɴᴠᴀʟɪᴅ ᴀʀɢᴜᴍᴇɴᴛ! ᴜsᴇ `on` ᴏʀ `off`\n\nᴇxᴀᴍᴘʟᴇ: `/auto_filter on` ᴏʀ `/auto_filter off`')

@Client.on_message(filters.command('pm_search') & filters.user(ADMINS))
async def pm_search_toggle(bot, message):
    if len(message.command) < 2:
        await message.reply('ᴜsᴀɢᴇ: /pm_search <on/off>\n\nᴇxᴀᴍᴘʟᴇ: `/pm_search on` ᴏʀ `/pm_search off`')
        return
    
    action = message.command[1].lower()
    
    if action == 'on':
        silicondb.update_bot_sttgs('PM_SEARCH', True)
        await message.reply('✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴛᴜʀɴᴇᴅ **ᴏɴ** ᴘᴍ sᴇᴀʀᴄʜ ғᴏʀ ᴀʟʟ ᴜsᴇʀs')
    elif action == 'off':
        silicondb.update_bot_sttgs('PM_SEARCH', False)
        await message.reply('❌ sᴜᴄᴄᴇssғᴜʟʟʏ ᴛᴜʀɴᴇᴅ **ᴏғғ** ᴘᴍ sᴇᴀʀᴄʜ ғᴏʀ ᴀʟʟ ᴜsᴇʀs')
    else:
        await message.reply('❗ ɪɴᴠᴀʟɪᴅ ᴀʀɢᴜᴍᴇɴᴛ! ᴜsᴇ `on` ᴏʀ `off`\n\nᴇxᴀᴍᴘʟᴇ: `/pm_search on` ᴏʀ `/pm_search off`')

@Client.on_message(filters.command('set_fsub'))
async def set_fsub(client, message):
    try:
        userid = message.from_user.id if message.from_user else None
        if not userid:
            return await message.reply("<b>You are Anonymous admin you can't use this command !</b>")
        if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            return await message.reply_text("ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴜsᴇᴅ ɪɴ ɢʀᴏᴜᴘs")
        grp_id = message.chat.id
        title = message.chat.title
        if not await is_check_admin(client, grp_id, userid):
            return await message.reply_text(script.NT_ADMIN_ALRT_TXT)
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            return await message.reply_text(
                "ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ!\n\n"
                "ᴄᴀɴ ᴀᴅᴅ ᴍᴜʟᴛɪᴘʟᴇ ᴄʜᴀɴɴᴇʟs sᴇᴘᴀʀᴀᴛᴇᴅ ʙʏ sᴘᴀᴄᴇs. ʟɪᴋᴇ: /sᴇᴛ_ғsᴜʙ ɪᴅ1 ɪᴅ2 ɪᴅ3\n"
            )
        option = args[1].strip()
        try:
            fsub_ids = [int(x) for x in option.split()]
        except ValueError:
            return await message.reply_text('ᴍᴀᴋᴇ sᴜʀᴇ ᴀʟʟ ɪᴅs ᴀʀᴇ ɪɴᴛᴇɢᴇʀs.')
        if len(fsub_ids) > 5:
            return await message.reply_text("ᴍᴀxɪᴍᴜᴍ 5 ᴄʜᴀɴɴᴇʟs ᴀʟʟᴏᴡᴇᴅ.")
        channels = "ᴄʜᴀɴɴᴇʟs:\n"
        channel_titles = []
        for id in fsub_ids:
            try:
                chat = await client.get_chat(id)
            except Exception as e:
                return await message.reply_text(
                    f"{id} ɪs ɪɴᴠᴀʟɪᴅ!\nᴍᴀᴋᴇ sᴜʀᴇ ᴛʜɪs ʙᴏᴛ ɪs ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.\n\nError - {e}"
                )
            if chat.type != enums.ChatType.CHANNEL:
                return await message.reply_text(f"{id} ɪs ɴᴏᴛ ᴀ ᴄʜᴀɴɴᴇʟ.")
            channel_titles.append(f"{chat.title} (`{id}`)")
            channels += f'{chat.title}\n'
        await save_group_settings(grp_id, 'fsub', fsub_ids)
        await message.reply_text(f"sᴜᴄᴄᴇssғᴜʟʟʏ sᴇᴛ ꜰꜱᴜʙ ᴄʜᴀɴɴᴇʟ(ꜱ) ғᴏʀ {title} ᴛᴏ\n\n{channels}")
        mention = message.from_user.mention if message.from_user else "Unknown"
        await client.send_message(
            LOG_API_CHANNEL,
            f"#Fsub_Channel_set\n\n"
            f"ᴜꜱᴇʀ - {mention} ꜱᴇᴛ ᴛʜᴇ ꜰᴏʀᴄᴇ ᴄʜᴀɴɴᴇʟ(ꜱ) ꜰᴏʀ {title}:\n\n"
            f"ꜰꜱᴜʙ ᴄʜᴀɴɴᴇʟ(ꜱ):\n" + '\n'.join(channel_titles)
        )
    except Exception as e:
        err_text = f"⚠️ Error in set_fSub :\n{e}"
        logger.error(err_text)
        await client.send_message(LOG_API_CHANNEL, err_text)

@Client.on_message(filters.command("del_msg") & filters.user(ADMINS))
async def del_msg(client, message):
    confirm_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Yes", callback_data="confirm_del_yes"),
        InlineKeyboardButton("No", callback_data="confirm_del_no")
    ]])
    sent_message = await message.reply_text(
        "⚠️ Aʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄʟᴇᴀʀ ᴛʜᴇ ᴜᴘᴅᴀᴛᴇs ʟɪsᴛ ?\n\n ᴅᴏ ʏᴏᴜ ꜱᴛɪʟʟ ᴡᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ?",
        reply_markup=confirm_markup
    )
    await asyncio.sleep(60)
    try:
        await sent_message.delete()
    except Exception as e:
        print(f"Error deleting the message: {e}")

@Client.on_callback_query(filters.regex('^confirm_del_'))
async def confirmation_handler(client, callback_query):
    action = callback_query.data.split("_")[-1] 
    if action == "yes":
        await db.delete_all_msg()  
        await callback_query.message.edit_text('🧹 ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ ʟɪsᴛ ʜᴀs ʙᴇᴇɴ ᴄʟᴇᴀʀᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ ✅')
    elif action == "no":
        await callback_query.message.delete()  
    await callback_query.answer()

@Client.on_message(filters.private & filters.command("movie_update") & filters.user(ADMINS))
async def set_movie_update_notification(client, message):
    bot_id = client.me.id
    try:
        option = message.text.split(" ", 1)[1].strip().lower()
        enable_status = option in ['on', 'true']
    except (IndexError, ValueError):
        await message.reply_text("<b>💔 Invalid option. Please send 'on' or 'off' after the command.</b>")
        return
    try:
        await db.update_movie_update_status(bot_id, enable_status)
        response_text = (
            "<b>ᴍᴏᴠɪᴇ ᴜᴘᴅᴀᴛᴇ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ ᴇɴᴀʙʟᴇᴅ ✅</b>" if enable_status 
            else "<b>ᴍᴏᴠɪᴇ ᴜᴘᴅᴀᴛᴇ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ ᴅɪꜱᴀʙʟᴇᴅ ❌</b>"
        )
        await message.reply_text(response_text)
    except Exception as e:
        logger.error(f"Error in set_movie_update_notification: {e}")


        await message.reply_text(f"<b>❗ An error occurred: {e}</b>")

@Client.on_message(filters.command('admin_cmd') & filters.user(ADMINS))
async def admin_commands(client, message):
    await message.reply_text(script.ADMIN_CMD_TXT, disable_web_page_preview=True)

@Client.on_message(filters.command('group_cmd'))
async def group_commands(client, message):
    await message.reply_text(script.GROUP_CMD, disable_web_page_preview=True)
