import logging
from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, ChatAdminRequired, PeerIdInvalid
from info import LONG_IMDB_DESCRIPTION, IS_VERIFY, START_IMG, LOG_CHANNEL
from imdb import Cinemagoer
import asyncio
from pyrogram.types import Message, ReplyKeyboardMarkup, InlineKeyboardButton
from pyrogram import enums
import pytz, re, os 
from shortzy import Shortzy
from datetime import datetime
from typing import Any
from database.users_chats_db import db
from database.extra_db import silicondb


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BANNED = {}
imdb = Cinemagoer() 
 
class temp(object):
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    CURRENT=int(os.environ.get("SKIP", 2))
    CANCEL = False
    U_NAME = None
    B_NAME = None
    B_LINK = None
    BOT = None
    FILES_ID = {}
    USERS_CANCEL = False
    GROUPS_CANCEL = False    
    CHAT = {}

def formate_file_name(file_name):
    file_name = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@') and not x.startswith('www.'), file_name.split()))
    return file_name

async def is_req_subscribed(bot, user_id, rqfsub_channels):
    btn = []
    for ch_id in rqfsub_channels:
        if await db.has_joined_channel(user_id, ch_id):
            continue
        try:
            member = await bot.get_chat_member(ch_id, user_id)
            if member.status != enums.ChatMemberStatus.BANNED:
                await db.add_join_req(user_id, ch_id)
                continue
        except UserNotParticipant:
            pass
        except Exception as e:
            logger.error(f"Error checking membership in {ch_id}: {e}")
        try:
            chat   = await bot.get_chat(ch_id)
            invite = await bot.create_chat_invite_link(
                ch_id,
                creates_join_request=True
            )
            btn.append([InlineKeyboardButton(f"⛔️ Join {chat.title}", url=invite.invite_link)])
        except ChatAdminRequired:
            logger.warning(f"Bot not admin in {ch_id}")
        except Exception as e:
            logger.warning(f"Invite link error for {ch_id}: {e}")     
    return btn

async def is_subscribed(bot, user_id, fsub_channels):
    btn = []
    for channel_id in fsub_channels:
        try:
            chat = await bot.get_chat(int(channel_id))
            await bot.get_chat_member(channel_id, user_id)
        except UserNotParticipant:
            try:
                invite = await bot.create_chat_invite_link(channel_id, creates_join_request=False)
                btn.append([InlineKeyboardButton(f"📢 Join {chat.title}", url=invite.invite_link)])
            except Exception as e:
                logger.warning(f"Failed to create invite for {channel_id}: {e}")
        except Exception as e:
            logger.exception(f"is_subscribed error for {channel_id}: {e}")
            pass
    return btn

async def process_trending_data(limit, format_type):
    messages = silicondb.get_silicon_messages(limit)
    validator = lambda text: bool(re.match('^[a-zA-Z0-9 ]*$', text))

    unique_searches = []
    seen = set()

    for msg in messages:
        normalized = msg.lower()
        if normalized not in seen and validator(msg):
            seen.add(normalized)
            truncate_len = 32 if format_type == "keyboard" else 32
            processed = msg[:truncate_len] + "..." if len(msg) > 35 else msg
            unique_searches.append(processed)

    return unique_searches

def create_keyboard_layout(searches):
    return [searches[i:i+2] for i in range(0, len(searches), 2)]

def extract_limit_from_command(command_parts, default):
    try:
        return int(command_parts[1]) if len(command_parts) > 1 else default
    except (IndexError, ValueError):
        return -1 if len(command_parts) > 1 else default

def generate_trend_list(searches):
    return "\n".join([f"{idx+1}. <b>{search}</b>" for idx, search in enumerate(searches)])

async def get_poster(query, bulk=False, id=False, file=None):
    if not id:
        query = (query.strip()).lower()
        title = query
        year = re.findall(r'[1-2]\d{3}$', query, re.IGNORECASE)
        if year:
            year = list_to_str(year[:1])
            title = (query.replace(year, "")).strip()
        elif file is not None:
            year = re.findall(r'[1-2]\d{3}', file, re.IGNORECASE)
            if year:
                year = list_to_str(year[:1]) 
        else:
            year = None
        movieid = imdb.search_movie(title.lower(), results=10)
        if not movieid:
            return None
        if year:
            filtered=list(filter(lambda k: str(k.get('year')) == str(year), movieid))
            if not filtered:
                filtered = movieid
        else:
            filtered = movieid
        movieid=list(filter(lambda k: k.get('kind') in ['movie', 'tv series'], filtered))
        if not movieid:
            movieid = filtered
        if bulk:
            return movieid
        movieid = movieid[0].movieID
    else:
        movieid = query
    movie = imdb.get_movie(movieid)
    if movie.get("original air date"):
        date = movie["original air date"]
    elif movie.get("year"):
        date = movie.get("year")
    else:
        date = "N/A"
    plot = ""
    if not LONG_IMDB_DESCRIPTION:
        plot = movie.get('plot')
        if plot and len(plot) > 0:
            plot = plot[0]
    else:
        plot = movie.get('plot outline')
    if plot and len(plot) > 800:
        plot = plot[0:800] + "..."

    return {
        'title': movie.get('title'),
        'votes': movie.get('votes'),
        "aka": list_to_str(movie.get("akas")),
        "seasons": movie.get("number of seasons"),
        "box_office": movie.get('box office'),
        'localized_title': movie.get('localized title'),
        'kind': movie.get("kind"),
        "imdb_id": f"tt{movie.get('imdbID')}",
        "cast": list_to_str(movie.get("cast")),
        "runtime": list_to_str(movie.get("runtimes")),
        "countries": list_to_str(movie.get("countries")),
        "certificates": list_to_str(movie.get("certificates")),
        "languages": list_to_str(movie.get("languages")),
        "director": list_to_str(movie.get("director")),
        "writer":list_to_str(movie.get("writer")),
        "producer":list_to_str(movie.get("producer")),
        "composer":list_to_str(movie.get("composer")) ,
        "cinematographer":list_to_str(movie.get("cinematographer")),
        "music_team": list_to_str(movie.get("music department")),
        "distributors": list_to_str(movie.get("distributors")),
        'release_date': date,
        'year': movie.get('year'),
        'genres': list_to_str(movie.get("genres")),
        'poster': movie.get('full-size cover url' , START_IMG),
        'plot': plot,
        'rating': str(movie.get("rating")),
        'url':f'https://www.imdb.com/title/tt{movieid}'
    }

async def users_broadcast(user_id, message, is_pin):
    try:
        m=await message.copy(chat_id=user_id)
        if is_pin:
            await m.pin(both_sides=True)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await users_broadcast(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} -Blocked the bot.")
        await db.delete_user(user_id)
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"

async def groups_broadcast(chat_id, message, is_pin):
    try:
        m = await message.copy(chat_id=chat_id)
        if is_pin:
            try:
                await m.pin()
            except:
                pass
        return "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await groups_broadcast(chat_id, message)
    except Exception as e:
        await db.delete_chat(chat_id)
        return "Error"

async def junk_group(chat_id, message):
    try:
        kk = await message.copy(chat_id=chat_id)
        await kk.delete(True)
        return True, "Succes", 'mm'
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await junk_group(chat_id, message)
    except Exception as e:
        await db.delete_chat(int(chat_id))       
        logging.info(f"{chat_id} - PeerIdInvalid")
        return False, "deleted", f'{e}\n\n'
    

async def clear_junk(user_id, message):
    try:
        key = await message.copy(chat_id=user_id)
        await key.delete(True)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await clear_junk(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"

async def get_settings(group_id):
    settings = await db.get_settings(group_id)
    return settings
  
async def save_group_settings(group_id, key, value):
    current = await get_settings(group_id)
    current.update({key: value})

    await db.update_settings(group_id, current)

def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def get_name(name):
    regex = re.sub(r'@\w+', '', name)
    return regex

def list_to_str(k):    
    if not k:
        return "N/A"
    elif len(k) == 1:
        return str(k[0])
    else:
        return ', '.join(str(item) for item in k)


async def get_shortlink(link, grp_id, is_second_shortener=False, is_third_shortener=False):
    settings = await get_settings(grp_id)
    
    if IS_VERIFY:
        if is_third_shortener:             
            api, site = settings['api_three'], settings['shortner_three']
        else:
            if is_second_shortener:
                api, site = settings['api_two'], settings['shortner_two']
            else:
                api, site = settings['api'], settings['shortner']
        
        shortzy = Shortzy(api, site)
        try:
            link = await shortzy.convert(link)
        except Exception as e:
            link = await shortzy.get_quick_link(link)
    
    return link 

def get_file_id(message: "Message") -> Any:
    media_types = (
        "audio",
        "document",
        "photo",
        "sticker",
        "animation",
        "video",
        "voice",
        "video_note",
    )    
    if message.media:
        for attr in media_types:
            media = getattr(message, attr, None)
            if media:
                setattr(media, "message_type", attr)
                return media

def get_hash(media_msg: Message) -> str:
    media = get_file_id(media_msg)
    return getattr(media, "file_unique_id", "")[:6]

def get_status():
    tz = pytz.timezone('Asia/Colombo')
    hour = datetime.now(tz).time().hour
    if 5 <= hour < 12:
        sts = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ"
    elif 12 <= hour < 18:
        sts = "ɢᴏᴏᴅ ᴀꜰᴛᴇʀɴᴏᴏɴ"
    else:
        sts = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ"
    return sts

async def is_check_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    except:
        return False

async def get_seconds(time_string):
    def extract_value_and_unit(ts):
        value = ""
        unit = ""
        index = 0
        while index < len(ts) and ts[index].isdigit():
            value += ts[index]
            index += 1
        unit = ts[index:].lstrip()
        if value:
            value = int(value)
        return value, unit
    value, unit = extract_value_and_unit(time_string)
    if unit == 's':
        return value
    elif unit == 'min':
        return value * 60
    elif unit == 'hour':
        return value * 3600
    elif unit == 'day':
        return value * 86400
    elif unit == 'month':
        return value * 86400 * 30
    elif unit == 'year':
        return value * 86400 * 365
    else:
        return 0

def get_readable_time(seconds):
    periods = [('days', 86400), ('hour', 3600), ('min', 60), ('sec', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)}{period_name}'
    return result


async def log_error(client, error_message):
    try:
        await client.send_message(
            chat_id=LOG_CHANNEL, 
            text=f"<b>⚠️ Error Log:</b>\n<code>{error_message}</code>"
        )
    except Exception as e:
        print(f"Failed to log error: {e}")
