import datetime
import pytz
from motor.motor_asyncio import AsyncIOMotorClient
from info import *

client = AsyncIOMotorClient(DATABASE_URI)
mydb = client[DATABASE_NAME]

class Database:

    def __init__(self):
        self.col = mydb.users
        self.grp = mydb.groups
        self.misc = mydb.misc
        self.verify_id = mydb.verify_id
        self.users = mydb.uersz
        self.req = mydb.requests
        self.grp_and_ids = mydb.grp_and_ids
        self.codes = mydb.codes
        self.movies_update_channel = mydb.movies_update_channel
        self.botcol = mydb.bot_settings
        self.movie_updates = mydb.movie_updates
        self.connection = mydb.connections

        self.default = {
            'spell_check': SPELL_CHECK,
            'auto_filter': AUTO_FILTER,
            'file_secure': PROTECT_CONTENT,
            'auto_delete': AUTO_DELETE,
            'template': IMDB_TEMPLATE,
            'caption': FILE_CAPTION,
            'tutorial': TUTORIAL,
            'tutorial_two': TUTORIAL2,
            'tutorial_three': TUTORIAL3,
            'shortner': SHORTENER_WEBSITE,
            'api': SHORTENER_API,
            'shortner_two': SHORTENER_WEBSITE2,
            'api_two': SHORTENER_API2,
            'log': LOG_VR_CHANNEL,
            'imdb': IMDB,
            'link': LINK_MODE, 
            'is_verify': IS_VERIFY, 
            'verify_time': TWO_VERIFY_GAP,
            'shortner_three': SHORTENER_WEBSITE3,
            'api_three': SHORTENER_API3,
            'third_verify_time': THREE_VERIFY_GAP,
            'fsub': AUTH_CHANNELS,
        }

    async def add_name(self, filename):
        if await self.movie_updates.find_one({'_id': filename}):
            return False
        await self.movie_updates.insert_one({'_id': filename})
        return True

    async def delete_all_msg(self):
        await self.movie_updates.delete_many({})
        print("All filenames notification have been deleted.")
        return True

    async def get_bot_setting(self, bot_id, setting_key, default_value):
        bot = await self.botcol.find_one({'id': int(bot_id)}, {setting_key: 1, '_id': 0})
        return bot[setting_key] if bot and setting_key in bot else default_value  

    async def update_bot_setting(self, bot_id, setting_key, value):
        await self.botcol.update_one(
            {'id': int(bot_id)}, 
            {'$set': {setting_key: value}}, 
            upsert=True
        )

    async def movie_update_status(self, bot_id):
        return await self.get_bot_setting(bot_id, 'MOVIE_UPDATE_NOTIFICATION', MOVIE_UPDATE_NOTIFICATION)

    async def update_movie_update_status(self, bot_id, enable):
        await self.update_bot_setting(bot_id, 'MOVIE_UPDATE_NOTIFICATION', enable)

    def new_user(self, id: int, name: str) -> dict:
        return {
            'id': id,
            'name': name,
            'ban_status': {
                'is_banned': False,
                'ban_reason': ""
            }
        }
    async def get_settings(self, id: int) -> dict:
        id = int(id) 
        chat = await self.grp.find_one({'id': id})
        if not chat:
            if id < 0:
                await self.grp.insert_one({'id': id, 'settings': self.default})
            return self.default
        return chat.get('settings', self.default)
    
    async def update_settings(self, id: int, settings: dict):
        await self.grp.update_one(
            {'id': id}, 
            {'$set': {'settings': settings}}, 
            upsert=True
        )
        
    async def find_join_req(self, id):
        return bool(await self.req.find_one({'id': id}))

    async def add_join_req(self, user_id: int, channel_id: int): #update
        await self.req.update_one(
            {'user_id': user_id},
            {
                '$addToSet': {'channels': channel_id},
                '$setOnInsert': {'created_at': datetime.datetime.utcnow()}
            },
            upsert=True
        )
        
    async def has_joined_channel(self, user_id: int, channel_id: int):
        doc = await self.req.find_one({'user_id': user_id})
        return doc and 'channels' in doc and channel_id in doc['channels']

    async def del_join_req(self):
        await self.req.drop()

    def new_group(self, id, title):
        return dict(
            id = id,
            title = title,
            chat_status=dict(
                is_disabled=False,
                reason=""
            )
        )
    
    async def remove_ban(self, id):
        ban_status = dict(
            is_banned=False,
            ban_reason=''
        )
        await self.col.update_one({'id': id}, {'$set': {'ban_status': ban_status}})

    async def ban_user(self, user_id, ban_reason="No Reason"):
        ban_status = dict(
            is_banned=True,
            ban_reason=ban_reason
        )
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        default = dict(
            is_banned=False,
            ban_reason=''
        )
        user = await self.col.find_one({'id': int(id)})
        if not user:
            return default
        return user.get('ban_status', default)

    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
        
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)
    
    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count
    
    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    async def delete_chat(self, id):
        await self.grp.delete_many({'id': int(id)})

    async def get_banned(self):
        users = self.col.find({'ban_status.is_banned': True})
        chats = self.grp.find({'chat_status.is_disabled': True})
    
        users_list = await users.to_list(length=None)
        chats_list = await chats.to_list(length=None)
    
        b_chats = [chat['id'] for chat in chats_list]
        b_users = [user['id'] for user in users_list]
    
        return b_users, b_chats

    async def disable_chat(self, chat, reason="No Reason"):
        chat_status = dict(
            is_disabled=True,
            reason=reason,
        )
        await self.grp.update_one({'id': int(chat)}, {'$set': {'chat_status': chat_status}})

    async def re_enable_chat(self, id):
        chat_status = dict(
            is_disabled=False,
            reason="",
        )
        await self.grp.update_one({'id': int(id)}, {'$set': {'chat_status': chat_status}})
    
    async def add_chat(self, chat, title):
        chat = self.new_group(chat, title)
        await self.grp.insert_one(chat)

    async def get_chat(self, chat):
        chat = await self.grp.find_one({'id':int(chat)})
        return False if not chat else chat.get('chat_status')  

    async def update_settings(self, id, settings):
        await self.grp.update_one({'id': int(id)}, {'$set': {'settings': settings}})   
    
    async def total_chat_count(self):
        count = await self.grp.count_documents({})
        return count
    
    async def get_all_chats(self):
        return self.grp.find({})

    async def get_db_size(self):
        return (await mydb.command("dbstats"))['dataSize'] 

    async def get_notcopy_user(self, user_id):
        user_id = int(user_id)
        user = await self.misc.find_one({"user_id": user_id})
        ist_timezone = pytz.timezone('Asia/Kolkata')
        if not user:
            res = {
                "user_id": user_id,
                "last_verified": datetime.datetime(2020, 5, 17, 0, 0, 0, tzinfo=ist_timezone),
                "second_time_verified": datetime.datetime(2019, 5, 17, 0, 0, 0, tzinfo=ist_timezone),
            }
            user = await self.misc.insert_one(res)
        return user

    async def update_notcopy_user(self, user_id, value:dict):
        user_id = int(user_id)
        myquery = {"user_id": user_id}
        newvalues = {"$set": value}
        return await self.misc.update_one(myquery, newvalues)

    async def is_user_verified(self, user_id):
        user = await self.get_notcopy_user(user_id)
        try:
            pastDate = user["last_verified"]
        except Exception:
            user = await self.get_notcopy_user(user_id)
            pastDate = user["last_verified"]
        ist_timezone = pytz.timezone('Asia/Kolkata')
        pastDate = pastDate.astimezone(ist_timezone)
        current_time = datetime.datetime.now(tz=ist_timezone)
        seconds_since_midnight = (current_time - datetime.datetime(current_time.year, current_time.month, current_time.day, 0, 0, 0, tzinfo=ist_timezone)).total_seconds()
        time_diff = current_time - pastDate
        total_seconds = time_diff.total_seconds()
        return total_seconds <= seconds_since_midnight

    async def user_verified(self, user_id):
        user = await self.get_notcopy_user(user_id)
        try:
            pastDate = user["second_time_verified"]
        except Exception:
            user = await self.get_notcopy_user(user_id)
            pastDate = user["second_time_verified"]
        ist_timezone = pytz.timezone('Asia/Kolkata')
        pastDate = pastDate.astimezone(ist_timezone)
        current_time = datetime.datetime.now(tz=ist_timezone)
        seconds_since_midnight = (current_time - datetime.datetime(current_time.year, current_time.month, current_time.day, 0, 0, 0, tzinfo=ist_timezone)).total_seconds()
        time_diff = current_time - pastDate
        total_seconds = time_diff.total_seconds()
        return total_seconds <= seconds_since_midnight

    async def use_second_shortener(self, user_id, time):
        user = await self.get_notcopy_user(user_id)
        if not user.get("second_time_verified"):
            ist_timezone = pytz.timezone('Asia/Kolkata')
            await self.update_notcopy_user(user_id, {"second_time_verified":datetime.datetime(2019, 5, 17, 0, 0, 0, tzinfo=ist_timezone)})
            user = await self.get_notcopy_user(user_id)
        if await self.is_user_verified(user_id):
            try:
                pastDate = user["last_verified"]
            except Exception:
                user = await self.get_notcopy_user(user_id)
                pastDate = user["last_verified"]
            ist_timezone = pytz.timezone('Asia/Kolkata')
            pastDate = pastDate.astimezone(ist_timezone)
            current_time = datetime.datetime.now(tz=ist_timezone)
            time_difference = current_time - pastDate
            if time_difference > datetime.timedelta(seconds=time):
                pastDate = user["last_verified"].astimezone(ist_timezone)
                second_time = user["second_time_verified"].astimezone(ist_timezone)
                return second_time < pastDate
        return False

    async def use_third_shortener(self, user_id, time):
        user = await self.get_notcopy_user(user_id)
        if not user.get("third_time_verified"):
            ist_timezone = pytz.timezone('Asia/Kolkata')
            await self.update_notcopy_user(user_id, {"third_time_verified":datetime.datetime(2018, 5, 17, 0, 0, 0, tzinfo=ist_timezone)})
            user = await self.get_notcopy_user(user_id)
        if await self.user_verified(user_id):
            try:
                pastDate = user["second_time_verified"]
            except Exception:
                user = await self.get_notcopy_user(user_id)
                pastDate = user["second_time_verified"]
            ist_timezone = pytz.timezone('Asia/Kolkata')
            pastDate = pastDate.astimezone(ist_timezone)
            current_time = datetime.datetime.now(tz=ist_timezone)
            time_difference = current_time - pastDate
            if time_difference > datetime.timedelta(seconds=time):
                pastDate = user["second_time_verified"].astimezone(ist_timezone)
                second_time = user["third_time_verified"].astimezone(ist_timezone)
                return second_time < pastDate
        return False
   
    async def create_verify_id(self, user_id: int, hash):
        res = {"user_id": user_id, "hash":hash, "verified":False}
        return await self.verify_id.insert_one(res)

    async def get_verify_id_info(self, user_id: int, hash):
        return await self.verify_id.find_one({"user_id": user_id, "hash": hash})

    async def update_verify_id_info(self, user_id, hash, value: dict):
        myquery = {"user_id": user_id, "hash": hash}
        newvalues = { "$set": value }
        return await self.verify_id.update_one(myquery, newvalues)

    async def get_user(self, user_id):
        user_data = await self.users.find_one({"id": user_id})
        return user_data
        
    async def update_user(self, user_data):
        await self.users.update_one({"id": user_data["id"]}, {"$set": user_data}, upsert=True)

    async def has_premium_access(self, user_id):
        user_data = await self.get_user(user_id)
        if user_data:
            expiry_time = user_data.get("expiry_time")
            if expiry_time is None:
                return False
            elif isinstance(expiry_time, datetime.datetime) and datetime.datetime.now() <= expiry_time:
                return True
            else:
                await self.users.update_one({"id": user_id}, {"$set": {"expiry_time": None}})
        return False
        
    async def update_one(self, filter_query, update_data):
        try:
            result = await self.users.update_one(filter_query, update_data)
            return result.matched_count == 1
        except Exception as e:
            print(f"Error updating document: {e}")
            return False

    async def get_expired(self, current_time):
        expired_users = []
        if data := self.users.find({"expiry_time": {"$lt": current_time}}):
            async for user in data:
                expired_users.append(user)
        return expired_users

    async def remove_premium_access(self, user_id):
        return await self.update_one(
            {"id": user_id}, {"$set": {"expiry_time": None}}
        )
    async def all_premium_users(self):
        count = await self.users.count_documents({
        "expiry_time": {"$gt": datetime.datetime.now()}
        })
        return count

    async def movies_update_channel_id(self , id=None):
        if id is None:
            myLinks = await self.movies_update_channel.find_one({})
            if myLinks is not None:
                return myLinks.get("id")
            else:
                return None
        return await self.movies_update_channel.update_one({} , {'$set': {'id': id}} , upsert=True)

    async def del_movies_channel_id(self):
        try: 
            isDeleted = await self.movies_update_channel.delete_one({})
            if isDeleted.deleted_count > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"Got err in db set : {e}")
            return False
    
    #group connection 
    async def connect_group(self, group_id: int, user_id: int):
        user = await self.connection.find_one({'_id': user_id})
        if user:
            await self.connection.update_one(
                {'_id': user_id},
                {"$addToSet": {"group_ids": group_id}}
            )
        else:
            await self.connection.insert_one(
                {'_id': user_id, 'group_ids': [group_id]}
            )
    async def get_connected_grps(self, user_id: int) -> list:
        user = await self.connection.find_one({'_id': user_id})
        return user.get("group_ids", []) if user else []

    async def disconnect_group(self, group_id: int, user_id: int):
        user = await self.connection.find_one({'_id': user_id})
        if user:
            await self.connection.update_one(
                {'_id': user_id},
                {"$pull": {"group_ids": group_id}}
            )

    # ------------------ FILE LIMIT FUNCTIONS ------------------

    async def get_user_limit_info(self, user_id: int):
        """Return user's file usage and reset time."""
        user = await self.users.find_one({'id': int(user_id)})
        if not user:
            # If new user, create entry
            user = {
                'id': int(user_id),
                'used_files': 0,
                'limit_reset_at': None
            }
            await self.users.insert_one(user)
        return {
            'used_files': user.get('used_files', 0),
            'limit_reset_at': user.get('limit_reset_at')
        }

    async def update_user_limit(self, user_id: int, used_files: int, limit_reset_at=None):
        """Update user's used file count and reset time."""
        update_data = {
            'used_files': used_files,
            'limit_reset_at': limit_reset_at
        }
        await self.users.update_one({'id': int(user_id)}, {'$set': update_data}, upsert=True)


db = Database()
