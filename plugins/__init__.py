import aiohttp
from asyncio import sleep 
from datetime import datetime
from database.users_chats_db import db
from info import LOG_CHANNEL, URL
from pyrogram.types import BotCommand

COMMANDS = {
    "start": "ꜱᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ.",
    "trendlist": "ɢᴇᴛ ᴛʀᴇɴᴅɪɴɢ ꜱᴇᴀʀᴄʜ ʟɪꜱᴛ.",
    "top_search": "ᴛᴏᴘ sᴇᴀʀᴄʜᴇs ᴏꜰ ᴅᴀʏ.",
    "myplan" : "ᴄʜᴇᴄᴋ ᴘʀᴇᴍɪᴜᴍ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ.",
    "plan" :"ᴄʜᴇᴄᴋ ᴘʀᴇᴍɪᴜᴍ ᴘʀɪᴄᴇ.",
    "settings": "ᴄʜᴀɴɢᴇ sᴇᴛᴛɪɴɢs.",
    "details": "ꜱᴇᴇ ɢʀᴏᴜᴘ ꜱᴇᴛᴛɪɴɢꜱ.",
    "id": "ᴄʜᴇᴄᴋ ʏᴏᴜʀ ɪᴅ.",
    "myplan": "sᴇᴇ ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴘʟᴀɴ.",
    "plan": "sᴇᴇ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ ᴘʀɪᴄᴇ.",
    "redeem": "ʀᴇᴇᴅᴇᴍ ᴀ ᴄᴏᴅᴇ.",
    "group_cmd": "ᴄʜᴇᴄᴋ ᴀʟʟ ɢʀᴏᴜᴘ ᴄᴏᴍᴍᴀɴᴅs.",
    "admin_cmd": "ᴄʜᴇᴄᴋ ᴀʟʟ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs.",
    "stats": "ᴄʜᴇᴄᴋ ʙᴏᴛ ꜱᴛᴀᴛᴜꜱ.",
    "broadcast": "ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ ᴛᴏ ᴜsᴇʀs.",
    "grp_broadcast": "ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ ᴛᴏ ɢʀᴏᴜᴘ.",
    "add_redeem": "ᴀᴅᴅ ʀᴇᴇᴅᴇᴍ ᴄᴏᴅᴇ.",
    "allcodes": "sᴇᴇ ᴀʟʟ ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇs.",
    "clearcodes": "ᴄʟᴇᴀʀ ᴀʟʟ ʀᴇᴇᴅᴇᴍ ᴄᴏᴅᴇ.",
    "add_premium": "ᴀᴅᴅ ᴜsᴇʀ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ʟɪsᴛ.",
    "check_plan": "ᴄʜᴇᴄᴋ ᴜsᴇʀ ᴄᴜʀʀᴇɴᴛ ᴘʟᴀɴ.",
    "remove_premium": "ʀᴇᴍᴏᴠᴇ ᴜsᴇʀ ꜰʀᴏᴍ ᴘʀᴇᴍɪᴜᴍ ʟɪsᴛ.",
    "leave": "ʀᴇᴍᴏᴠᴇ ʙᴏᴛ ꜰʀᴏᴍ ɢʀᴏᴜᴘ.",
    "ban_user": "ʙᴀɴ ᴛʜᴇ ᴜsᴇʀ.",
    "unban_user": "ᴜɴʙᴀɴ ᴛʜᴇ ᴜsᴇʀ.",
    "ban_grp": "ʙᴀɴ ᴛʜᴇ ɢʀᴏᴜᴘ.",
    "unban_grp": "ᴜɴʙᴀɴ ᴛʜᴇ ɢʀᴏᴜᴘ.",
    "clear_junk": "ᴄʟᴇᴀʀ ᴀʟʟ ᴅᴇʟᴇᴛᴇᴅ ᴜsᴇʀ ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ.",
    "junk_group": "ᴄʟᴇᴀʀ ᴜɴ-ᴜsᴇᴅ ɢʀᴏᴜᴘ.",
    "groups": "sᴇᴇ ɢʀᴏᴜᴘ ʟɪsᴛ ᴡʜᴇʀᴇ ʙᴏᴛ ɪs ᴀᴅᴍɪɴ.",
    "delete": "ᴅᴇʟᴇᴛᴇ ꜱᴘᴇᴄɪꜰɪᴄ ꜰɪʟᴇs ꜰʀᴏᴍ ᴅʙ.",
    "deleteall": "ᴅᴇʟᴇᴛᴇ ᴀʟʟ ꜰɪʟᴇs ꜰʀᴏᴍ ᴅʙ.",
    "delreq": "ᴅᴇʟᴇᴛᴇ ᴀʟʟ ᴊᴏɪɴ ʀᴇǫ ғʀᴏᴍ ᴅʙ.",
    "del_msg": "ᴅᴇʟᴇᴛᴇ ᴀʟʟ ᴜᴘᴅᴀᴛᴇ ᴍᴇssᴀɢᴇ ꜰʀᴏᴍ ᴅʙ.",
    "movie_update": "ᴍᴏᴠɪᴇ ᴜᴘᴅᴀᴛᴇ ᴏɴ/ᴏꜰꜰ ᴀᴄᴄᴏʀᴅɪɴɢ ʏᴏᴜʀ ɴᴇᴇᴅᴇᴅ...",
    "pm_search": "ᴘᴍ sᴇᴀʀᴄʜ ᴏɴ/ᴏꜰꜰ ᴀᴄᴄᴏʀᴅɪɴɢ ʏᴏᴜʀ ɴᴇᴇᴅᴇᴅ...",
    "auto_filter": "ᴀᴜᴛᴏ ғɪʟᴛᴇʀ ᴏɴ/ᴏꜰꜰ ᴀᴄᴄᴏʀᴅɪɴɢ ʏᴏᴜʀ ɴᴇᴇᴅᴇᴅ..."
}

async def check_expired_premium(client):
    while 1:
        data = await db.get_expired(datetime.now())
        for user in data:
            user_id = user["id"]
            await db.remove_premium_access(user_id)
            try:
                user = await client.get_users(user_id)
                await client.send_message(
                    chat_id=user_id,
                    text=f"<b>ʜᴇʏ {user.mention},\n\nʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss ʜᴀs ᴇxᴘɪʀᴇᴅ, ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴜsɪɴɢ ᴏᴜʀ sᴇʀᴠɪᴄᴇ 😊\n\nɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴛᴀᴋᴇ ᴛʜᴇ ᴘʀᴇᴍɪᴜᴍ ᴀɢᴀɪɴ, ᴛʜᴇɴ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ /plan ꜰᴏʀ ᴛʜᴇ ᴅᴇᴛᴀɪʟs ᴏꜰ ᴛʜᴇ ᴘʟᴀɴs...</b>"
                )
                await client.send_message(LOG_CHANNEL, text=f"<b>#Premium_Expire\n\nUser name: {user.mention}\nUser id: <code>{user_id}</code>")
            except Exception as e:
                print(e)
            await sleep(0.5)
        await sleep(1)

async def set_silicon_commands(client):
    try:
        commands = [BotCommand(cmd, desc) for cmd, desc in COMMANDS.items()]
        await client.set_bot_commands(commands)
        print("✅ Bot commands updated successfully!")
    except Exception as e:
        print(f"❌ Error setting bot commands: {e}")

async def keep_alive():
    async with aiohttp.ClientSession() as session:
        while True:
            await sleep(298)
            try:
                async with session.get(URL) as resp:
                    if resp.status != 200:
                        print(f"⚠️ Ping Error! Status: {resp.status}")
            except Exception as e:
                print(f"❌ Ping Failed: {e}")   
