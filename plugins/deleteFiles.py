import re
import logging
from pyrogram import Client, filters
from info import DELETE_CHANNELS, LOG_CHANNEL
from database.ia_filterdb import is_second_db_configured, second_collection, collection, unpack_new_file_id

logger = logging.getLogger(__name__)

media_filter = filters.document | filters.video | filters.audio

@Client.on_message(filters.chat(DELETE_CHANNELS) & media_filter)
async def deletemultiplemedia(bot, message):
    media = getattr(message, message.media.value, None)
    if media and media.mime_type in ['video/mp4', 'video/x-matroska']:
        file_id = unpack_new_file_id(media.file_id)
        deleted_count = await delete_file_by_id(file_id)
        if deleted_count:
            logger.info(f"File {media.file_name} with ID {file_id} deleted from database(s)")
        else:
            logger.warning(f"File {media.file_name} with ID {file_id} not found in database(s)")


async def delete_file_by_id(file_id: str):
    total_deleted = 0
    try:
        result1 = await collection.delete_one({"_id": file_id})
        total_deleted += result1.deleted_count

        if is_second_db_configured():
            result2 = await second_collection.delete_one({"_id": file_id})
            total_deleted += result2.deleted_count

        if total_deleted:
            logger.info(f"Deleted {total_deleted} document(s) with _id: {file_id}")
        else:
            logger.warning(f"No documents found with _id: {file_id} to delete")

    except Exception as e:
        logger.error(f"Error deleting document with _id {file_id}: {e}")
        return 0

    return total_deleted
