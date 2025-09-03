import os
import requests
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import get_file_id

def upload_image_requests(image_path):
    upload_url = "https://envs.sh"

    try:
        with open(image_path, 'rb') as file:
            files = {'file': file} 
            response = requests.post(upload_url, files=files)

            if response.status_code == 200:
                return response.text.strip() 
            else:
                raise Exception(f"Upload failed with status code {response.status_code}")

    except Exception as e:
        print(f"Error during upload: {e}")
        return None

@Client.on_message(filters.command("upload") & filters.private)
async def upload_command(client, message):
    replied = message.reply_to_message
    if not replied:
        await message.reply_text("⚠️ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴘʜᴏᴛᴏ ᴏʀ ᴠɪᴅᴇᴏ ᴜɴᴅᴇʀ 5 ᴍʙ")
        return

    file_info = get_file_id(replied)
    if not file_info:
        await message.reply_text("ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ 😑")
        return


    if replied.media and hasattr(replied, 'file_size'):
        if replied.file_size > 5242880:  # 5MB in bytes
            await message.reply_text("⚠️ ꜰɪʟᴇ sɪᴢᴇ ɪs ɢʀᴇᴀᴛᴇʀ ᴛʜᴀɴ 5 ᴍʙ")
            return

    silicon_path = await replied.download()

    uploading_message = await message.reply_text("<code>ᴘʀᴏᴄᴇssɪɴɢ....</code>", disable_web_page_preview=True)

    try:
        silicon_url = upload_image_requests(silicon_path)
        if not silicon_url:
            raise Exception("Failed to upload file.")
        
        await uploading_message.edit_text("<code>ᴅᴏɴᴇ :)</code>", disable_web_page_preview=True)
        
    except Exception as error:
        print(error)
        await uploading_message.edit_text(text=f"Error :- {error}", disable_web_page_preview=True)
        await asyncio.sleep(3)
        return await uploading_message.delete()

    try:
        os.remove(silicon_path)
    except Exception as error:
        print(f"Error removing file: {error}")

    await uploading_message.delete()
    
    await message.reply_text(
        text=f"<b>ʏᴏᴜʀ ᴜᴘʟᴏᴀᴅ ʟɪɴᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ 👇</b>\n\n<code>{silicon_url}</code>\n\n<b>ᴘᴏᴡᴇʀᴇᴅ ʙʏ - @Silicon_Bot_Update</b>",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(text="✓ ᴏᴘᴇɴ ʟɪɴᴋ ✓", url=silicon_url),
            InlineKeyboardButton(text="📱 sʜᴀʀᴇ ʟɪɴᴋ", url=f"https://telegram.me/share/url?url={silicon_url}")
        ], [
            InlineKeyboardButton(text="❌ ᴄʟᴏsᴇ ❌", callback_data="close_data")
        ]])
    )
