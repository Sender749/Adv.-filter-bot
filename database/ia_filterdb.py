import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from pymongo import MongoClient, TEXT
from pymongo.errors import DuplicateKeyError, OperationFailure
from info import USE_CAPTION_FILTER, FILES_DATABASE_URL, SECOND_FILES_DATABASE_URL, DATABASE_NAME, COLLECTION_NAME, MAX_BTN

logger = logging.getLogger(__name__)

client = MongoClient(FILES_DATABASE_URL)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]
filter_words_collection = db["filter_words"]
second_collection = None

try:
    collection.create_index([("file_name", TEXT), ("caption", TEXT)])
except OperationFailure as e:
    if "already exists" not in str(e):
        raise e

        if not SECOND_FILES_DATABASE_URL:
            logger.error('Your FILES_DATABASE_URL is full; please add SECOND_FILES_DATABASE_URL.')
        else:
            logger.info('Primary DB full, using SECOND_FILES_DATABASE_URL.')
    else:
        logger.exception(e)

if SECOND_FILES_DATABASE_URL:
    second_client = MongoClient(SECOND_FILES_DATABASE_URL)
    second_db = second_client[DATABASE_NAME]
    second_collection = second_db[COLLECTION_NAME]
try:
    second_collection.create_index([("file_name", TEXT), ("caption", TEXT)])
except OperationFailure as e:
    if "already exists" not in str(e):
        raise e

# -------------------------------------------------------------------

def get_filter_words():
    try:
        doc = filter_words_collection.find_one({"_id": "filter_words"})
        return set(doc["words"]) if doc else set()
    except Exception as e:
        logger.error(f"Error getting filter words: {e}")
        return set()

def set_filter_words(words):
    try:
        filter_words_collection.update_one(
            {"_id": "filter_words"},
            {"$set": {"words": list(words)}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error setting filter words: {e}")

def clean_query(query, filter_words):
    if not query or not filter_words:
        return query
    pattern = r'\b(?:' + '|'.join(map(re.escape, filter_words)) + r')\b'
    cleaned = re.sub(pattern, '', query, flags=re.IGNORECASE)
    return ' '.join(cleaned.split()).strip()

# -------------------------------------------------------------------

def is_second_db_configured() -> bool:
    return bool(SECOND_FILES_DATABASE_URL and second_collection is not None)

def second_db_count_documents():
     return second_collection.count_documents({})

def db_count_documents():
     return collection.count_documents({})

# -------------------------------------------------------------------

async def save_file(media):
    file_id = unpack_new_file_id(media.file_id)
    
    # Clean file name and caption safely
    file_name = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(media.file_name or "")).strip()
    file_caption = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(media.caption or "")).strip()

    # Combine both for text searching
    document = {
        '_id': file_id,
        'file_name': file_name,
        'file_size': media.file_size,
        'caption': file_caption
    }

    try:
        collection.insert_one(document)
        logger.info(f"Saved → {file_name or '(no name)'}")
        return 'suc'
    except DuplicateKeyError:
        logger.warning(f"Already saved → {file_name}")
        return 'dup'
    except OperationFailure:
        if SECOND_FILES_DATABASE_URL:
            try:
                second_collection.insert_one(document)
                logger.info(f"Saved to 2nd DB → {file_name}")
                return 'suc'
            except DuplicateKeyError:
                logger.warning(f"Already saved in 2nd DB → {file_name}")
                return 'dup'
        else:
            logger.error("Primary DB full, add SECOND_FILES_DATABASE_URL.")
            return 'err'

# -------------------------------------------------------------------

async def get_search_results(query, max_results=MAX_BTN, offset=0, lang=None):
    query = str(query).strip()
    filter_words = get_filter_words()
    query = clean_query(query, filter_words)
    if not query:
        query = '.'

    try:
        regex = re.compile(query, re.IGNORECASE)
    except:
        regex = re.compile(re.escape(query), re.IGNORECASE)

    # 🔍 Search both file_name and caption
    search_filter = {'$or': [{'file_name': regex}, {'caption': regex}]}

    # Use primary DB
    results = list(collection.find(search_filter, {'_id': 1, 'file_name': 1, 'file_size': 1, 'caption': 1}).limit(max_results * 2))

    # Merge second DB results if available
    if SECOND_FILES_DATABASE_URL:
        results += list(second_collection.find(search_filter, {'_id': 1, 'file_name': 1, 'file_size': 1, 'caption': 1}).limit(max_results * 2))

    # Filter by language if required
    if lang:
        results = [r for r in results if lang.lower() in (r.get('file_name', '').lower() + ' ' + r.get('caption', '').lower())]

    total_results = len(results)
    files = results[offset:offset + max_results]
    next_offset = offset + max_results if offset + max_results < total_results else ''
    
    return files, next_offset, total_results

# -------------------------------------------------------------------

async def delete_files(query):
    query = query.strip()
    regex = re.compile(query, re.IGNORECASE)
    filter_q = {'$or': [{'file_name': regex}, {'caption': regex}]}

    result1 = collection.delete_many(filter_q)
    total_deleted = result1.deleted_count

    if SECOND_FILES_DATABASE_URL:
        result2 = second_collection.delete_many(filter_q)
        total_deleted += result2.deleted_count

    return total_deleted

# -------------------------------------------------------------------

async def get_file_details(query):
    file_details = collection.find_one({'_id': query})
    if not file_details and SECOND_FILES_DATABASE_URL:
        file_details = second_collection.find_one({'_id': query})
    return file_details

# -------------------------------------------------------------------

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    return file_id
