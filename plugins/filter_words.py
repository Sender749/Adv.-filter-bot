from pyrogram import Client, filters
from info import ADMINS
from database.ia_filterdb import get_filter_words, set_filter_words
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("filterword") & filters.user(ADMINS))
async def show_filter_words(client, message):
    """Show all currently active filter words."""
    try:
        words = await get_filter_words()
        if not words:
            await message.reply_text("📝 No filter words set yet.\nUse `/set_filterword word1, word2` to add some.")
            return
        
        formatted_words = ", ".join(sorted(words))
        count = len(words)
        await message.reply_text(
            f"📝 **Current filter words** ({count}):\n\n"
            f"{formatted_words}\n\n"
            "To add more: `/set_filterword send, movie, series`"
        )
    except Exception as e:
        logger.exception("Error in show_filter_words:")
        await message.reply_text("❌ Error fetching filter words.")


@Client.on_message(filters.command("set_filterword") & filters.user(ADMINS))
async def update_filter_words(client, message):
    """Add new filter words or phrases to the database."""
    try:
        if len(message.command) < 2:
            example = "/set_filterword send, kr do, movie, series hai bhai, pls"
            await message.reply_text(
                f"❌ Please provide words/phrases separated by commas.\n\n"
                f"Example:\n`{example}`"
            )
            return
        
        # Extract new words
        new_words_raw = message.text.split(maxsplit=1)[1]
        new_words = {w.strip().lower() for w in new_words_raw.split(",") if w.strip()}

        if not new_words:
            await message.reply_text("❌ No valid words found to add.")
            return
        
        # Merge with existing set
        existing_words = await get_filter_words()
        updated_words = existing_words.union(new_words)
        await set_filter_words(updated_words)
        
        added_count = len(updated_words) - len(existing_words)
        await message.reply_text(
            f"✅ **Filter words updated successfully!**\n"
            f"- Total words: `{len(updated_words)}`\n"
            f"- Newly added: `{added_count}`\n\n"
            "Use `/filterword` to view all."
        )
    except Exception as e:
        logger.exception("Error in update_filter_words:")
        await message.reply_text("❌ Failed to update filter words. Please check logs.")


@Client.on_message(filters.command("removefilterword") & filters.user(ADMINS))
async def remove_filter_words(client, message):
    """Remove one or more filter words."""
    try:
        if len(message.command) < 2:
            await message.reply_text("❌ Please provide one or more words to remove.\nExample: `/removefilterword movie, send`")
            return

        # Extract words to remove
        remove_words_raw = message.text.split(maxsplit=1)[1]
        remove_words = {w.strip().lower() for w in remove_words_raw.split(",") if w.strip()}

        existing_words = await get_filter_words()
        before_count = len(existing_words)

        updated_words = existing_words.difference(remove_words)
        await set_filter_words(updated_words)
        removed_count = before_count - len(updated_words)

        if removed_count > 0:
            await message.reply_text(f"✅ Removed `{removed_count}` words.\nUse `/filterword` to view remaining.")
        else:
            await message.reply_text("⚠️ None of the provided words were found in the list.")
    except Exception as e:
        logger.exception("Error in remove_filter_words:")
        await message.reply_text("❌ Failed to remove filter words.")
