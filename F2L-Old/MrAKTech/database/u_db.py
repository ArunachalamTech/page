# Copyright 2021 To 2024-present, Author: MrAKTech

import datetime
import motor.motor_asyncio
from MrAKTech.config import Telegram
from MrAKTech.tools.txt import tamilxd


class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        self.su = self.db.StorageUsers
        self.black = self.db.blacklist
        self.chl = self.db.ChannelsList
        self.warn = self.db.WarnsList
        self.bot = self.db.bots
        self.Inactive = self.db.InActiveUsers

    def new_user(self, id):
        import secrets
        # Generate a random page code for privacy (8 characters)
        page_code = secrets.token_urlsafe(8)
        
        return dict(
            id=id,
            join_date=datetime.date.today().isoformat(),
            shortener_api=None,
            shortener_url=None,
            method="links",
            caption=tamilxd.STREAM_MSG_TXT,
            settings=None,
            storage="Off",
            auto_extract=True,  # Enable auto extraction by default
            # Linkmode fields
            linkmode=False,  # Default linkmode is off
            linkmode_captions={
                "caption1": None,
                "caption2": None,
                "caption3": None,
                "active_caption": None  # Which caption to use (1, 2, or 3)
            },
            shortlinks={
                "shortlink1": {"url": None, "api": None},
                "shortlink2": {"url": None, "api": None},
                "shortlink3": {"url": None, "api": None}
            },
            # Store files for batch processing
            pending_files=[],
            # User state for multi-step operations
            user_state=None,
            # Page mode settings
            page_mode=False,  # Default page mode is off
            page_shortlinks={
                "shortlink1": {"url": None, "api": None},
                "shortlink2": {"url": None, "api": None},
                "shortlink3": {"url": None, "api": None}
            },
            # Page mode customization
            page_settings={
                "shortlink_tutorials": {
                    "shortlink1": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"},
                    "shortlink2": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"},
                    "shortlink3": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"}
                },
                "button_visibility": {
                    "watch": True,
                    "download": True,
                    "telegram": True
                },
                "button_names": {
                    "watch": "🎮 Watch Online",
                    "download": "📥 Download",
                    "telegram": "📱 Telegram Storage"
                },
                "custom_buttons": []  # List of custom buttons with name, url, icon
            },
            # Random code for web links instead of user ID
            page_code=page_code,
            # Verify functionality fields
            verify_mode=False,  # Default verify mode is off
            verify_shortlinks={
                "shortlink1": {"url": None, "api": None},
                "shortlink2": {"url": None, "api": None},
                "shortlink3": {"url": None, "api": None}
            },
            # Verify mode customization
            verify_settings={
                "shortlink_tutorials": {
                    "shortlink1": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                    "shortlink2": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                    "shortlink3": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"}
                }
            },
            verify_time_gap=14400,  # 4 hours in seconds
            verification_status={
                "last_verified": None,
                "second_verified": None,
                "third_verified": None,
                "verify_count_today": 0,
                "last_reset_date": None
            }
        )

    async def add_user(self, id):
        user = self.new_user(id)
        await self.col.insert_one(user)

    async def get_user(self, id):
        return await self.col.find_one({"id": id})

    async def is_user_exist(self, id):
        user = await self.col.find_one({"id": int(id)})
        return bool(user)

    async def total_users_count(self):
        return await self.col.count_documents({})

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({"id": int(user_id)})

    # testing start

    async def get_user_details(self, user_id: int):
        return await self.col.find_one({"id": int(user_id)})

    async def set_caption(self, id, caption):
        await self.col.update_one({"id": id}, {"$set": {"caption": caption}})

    async def get_caption(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("caption", None)

    async def set_shortner_url(self, id, caption):
        await self.col.update_one({"id": id}, {"$set": {"shortener_url": caption}})

    async def get_shortner_url(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("shortener_url", None)

    async def set_shortner_api(self, id, caption):
        await self.col.update_one({"id": id}, {"$set": {"shortener_api": caption}})

    async def get_shortner_api(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("shortener_api", None)

    async def change_uploadmode(self, id, mode):
        await self.col.update_one({"id": id}, {"$set": {"method": mode}})

    async def get_uploadmode(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("method", None)

    async def change_storagemode(self, id, mode):
        await self.col.update_one({"id": id}, {"$set": {"storage": mode}})

    async def get_storagemode(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("storage", None)

    async def update_user_info(self, user_id, value: dict, tag="$set"):
        user_id = int(user_id)
        myquery = {"id": user_id}
        newvalues = {tag: value}
        await self.col.update_one(myquery, newvalues)

    async def reset_settings(self, id):
        await self.col.update_one(
            {"id": id},
            {
                "$set": {
                    "shortener_api": None,
                    "shortener_url": None,
                    "method": "links",
                    "caption": tamilxd.STREAM_MSG_TXT,
                    "linkmode": False,
                    "linkmode_captions": {
                        "caption1": None,
                        "caption2": None,
                        "caption3": None,
                        "active_caption": None
                    },
                    "shortlinks": {
                        "shortlink1": {"url": None, "api": None},
                        "shortlink2": {"url": None, "api": None},
                        "shortlink3": {"url": None, "api": None}
                    },
                    "pending_files": [],
                    "user_state": None
                }
            },
        )

    async def is_settings(self, id):
        user = await self.col.find_one({"id": int(id)})
        if (
            user["method"] == "links"
            and user["shortener_api"] is None
            and user["shortener_url"] is None
        ):
            if user["caption"] == tamilxd.STREAM_MSG_TXT:
                return False
        return True

    # Channel Database Codes

    default_setgs = {
        "api": None,
        "url": None,
        "shortlink": False,
        "method": "Button",
        "caption": tamilxd.STREAM_TXT,
        "replace": None,
        "page_mode": False,  # Default page mode is off
        "page_shortlinks": {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        },
        # Page mode customization for channels
        "page_settings": {
            "shortlink_tutorials": {
                "shortlink1": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"},
                "shortlink2": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"},
                "shortlink3": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"}
            },
            "button_visibility": {
                "watch": True,
                "download": True,
                "telegram": True
            },
            "button_names": {
                "watch": "🎮 Watch Online",
                "download": "📥 Download",
                "telegram": "📱 Telegram Storage"
            },
            "custom_buttons": []  # List of custom buttons with name, url, icon
        },
        "verify_mode": False,  # Default verify mode is off
        "verify_shortlinks": {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        },
        # Verify mode customization for channels
        "verify_settings": {
            "shortlink_tutorials": {
                "shortlink1": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                "shortlink2": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                "shortlink3": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"}
            }
        },
        "verify_time_gap": 14400  # 4 hours in seconds
    }

    async def in_channel(self, user_id: int, chat_id : int) -> bool:
        channel = await self.chl.find_one({"user_id": int(user_id), "chat_id": int(chat_id)})
        return bool(channel)

    async def add_channel(self, user_id: int, chat_id : int, title, username):
        channel = await self.in_channel(int(user_id), int(chat_id))
        if channel:
            return False
        
        import secrets
        # Generate a random page code for privacy (8 characters)
        page_code = secrets.token_urlsafe(8)
        
        return await self.chl.insert_one(
            {
                "user_id": int(user_id),
                "chat_id": int(chat_id),
                "title": title,
                "username": username,
                "settings": self.default_setgs,
                "page_code": page_code,
            }
        )

    async def remove_channel(self, user_id: int, chat_id : int):
        channel = await self.in_channel(int(user_id), int(chat_id))
        if not channel:
            return False
        return await self.chl.delete_many({"user_id": int(user_id), "chat_id": int(chat_id)})

    async def is_channel_exist(self, chat_id):
        channel = await self.chl.find_one({"chat_id": int(chat_id)})
        return bool(channel)

    async def get_channel_details(self, user_id: int, chat_id : int):
        return await self.chl.find_one({"user_id": int(user_id), "chat_id": int(chat_id)})

    async def get_user_channels(self, user_id: int):
        channels = self.chl.find({"user_id": int(user_id)})
        return [channel async for channel in channels]

    async def get_chl_settings(self, chat_id : int):
        chat = await self.chl.find_one({"chat_id": int(chat_id)})
        return chat.get("settings", self.default_setgs) if chat else self.default_setgs

    async def update_chl_settings(self, chat_id : int, type, value):
        await self.chl.update_one(
            {"chat_id": int(chat_id)}, {"$set": {f"settings.{type}": value}}
        )

    async def get_channel_detail(self, chat_id : int):
        return await self.chl.find_one({"chat_id": int(chat_id)})

    async def total_channels_count(self):
        return await self.chl.count_documents({})

    async def reset_chl_settings(self, chat_id : int):
        await self.chl.update_one(
            {"chat_id": int(chat_id)}, {"$set": {"settings": self.default_setgs}}
        )

    async def is_chl_settings(self, chat_id):
        chat = await self.get_chl_settings(chat_id)
        if chat["url"] is None and chat["api"] is None:
            if chat["caption"] == tamilxd.STREAM_TXT and chat["method"] == "Button":
                return False
        return True

    async def get_all_chat(self):
        return self.chl.find({})

    async def update_chat(self, id, chat_id):
        await self.col.update_one({"_id": id}, {"$set": {"chat_id": int(chat_id)}})

    # Page mode methods for channels
    async def set_chl_page_mode(self, chat_id, enabled):
        await self.chl.update_one(
            {"chat_id": int(chat_id)}, 
            {"$set": {"settings.page_mode": enabled}}
        )
    
    async def get_chl_page_mode(self, chat_id):
        chat = await self.chl.find_one({"chat_id": int(chat_id)})
        if chat and chat.get("settings"):
            return chat["settings"].get("page_mode", False)
        return False
    
    async def set_chl_page_shortlink(self, chat_id, shortlink_num, url, api):
        key = f"settings.page_shortlinks.shortlink{shortlink_num}"
        await self.chl.update_one(
            {"chat_id": int(chat_id)}, 
            {"$set": {f"{key}.url": url, f"{key}.api": api}}
        )
    
    async def get_chl_page_shortlinks(self, chat_id):
        chat = await self.chl.find_one({"chat_id": int(chat_id)})
        if chat and chat.get("settings") and chat["settings"].get("page_shortlinks"):
            return chat["settings"]["page_shortlinks"]
        return {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        }
    
    async def remove_chl_page_shortlink(self, chat_id, shortlink_num):
        key = f"settings.page_shortlinks.shortlink{shortlink_num}"
        await self.chl.update_one(
            {"chat_id": int(chat_id)}, 
            {"$set": {f"{key}.url": None, f"{key}.api": None}}
        )

    async def get_chl_page_code(self, chat_id):
        chat = await self.chl.find_one({"chat_id": int(chat_id)})
        return chat.get("page_code") if chat else None
    
    async def regenerate_chl_page_code(self, chat_id):
        import secrets
        new_page_code = secrets.token_urlsafe(8)
        await self.chl.update_one({"chat_id": int(chat_id)}, {"$set": {"page_code": new_page_code}})
        return new_page_code
    
    async def get_channel_by_page_code(self, page_code):
        return await self.chl.find_one({"page_code": page_code})

    # bot testing end

    async def get_bot(self, user_id: int):
        bot = await self.bot.find_one({"user_id": user_id})
        return bot if bot else None

    async def total_users_bots_count(self):
        count = await self.bot.count_documents({})
        return count

    # ----------------------ban, check banned or unban user----------------------

    def black_user(self, id):
        return dict(id=id, ban_date=datetime.date.today().isoformat())

    async def ban_user(self, id):
        user = self.black_user(id)
        await self.black.insert_one(user)

    async def unban_user(self, id):
        await self.black.delete_one({"id": int(id)})

    async def is_user_banned(self, id):
        user = await self.black.find_one({"id": int(id)})
        return True if user else False

    async def total_banned_users_count(self):
        count = await self.black.count_documents({})
        return count

    # Auto extraction methods
    async def set_auto_extract(self, id, enabled):
        await self.col.update_one({"id": id}, {"$set": {"auto_extract": enabled}})

    async def get_auto_extract(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("auto_extract", True)

    # Linkmode methods
    async def set_linkmode(self, id, enabled):
        await self.col.update_one({"id": id}, {"$set": {"linkmode": enabled}})

    async def get_linkmode(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("linkmode", False)

    async def set_linkmode_caption(self, id, caption_num, caption_text):
        await self.col.update_one({"id": id}, {"$set": {f"linkmode_captions.caption{caption_num}": caption_text}})

    async def get_linkmode_caption(self, id, caption_num):
        user = await self.col.find_one({"id": int(id)})
        captions = user.get("linkmode_captions", {})
        return captions.get(f"caption{caption_num}", None)

    async def set_active_linkmode_caption(self, id, caption_num):
        await self.col.update_one({"id": id}, {"$set": {"linkmode_captions.active_caption": caption_num}})

    async def get_active_linkmode_caption(self, id):
        user = await self.col.find_one({"id": int(id)})
        captions = user.get("linkmode_captions", {})
        return captions.get("active_caption", None)

    async def delete_linkmode_caption(self, id, caption_num):
        await self.col.update_one({"id": id}, {"$set": {f"linkmode_captions.caption{caption_num}": None}})

    async def set_shortlink(self, id, shortlink_num, url, api):
        await self.col.update_one({"id": id}, {"$set": {f"shortlinks.shortlink{shortlink_num}": {"url": url, "api": api}}})

    async def get_shortlink(self, id, shortlink_num):
        user = await self.col.find_one({"id": int(id)})
        shortlinks = user.get("shortlinks", {})
        return shortlinks.get(f"shortlink{shortlink_num}", {"url": None, "api": None})

    async def delete_shortlink(self, id, shortlink_num):
        await self.col.update_one({"id": id}, {"$set": {f"shortlinks.shortlink{shortlink_num}": {"url": None, "api": None}}})

    async def get_all_shortlinks(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("shortlinks", {})

    # Page mode methods for users
    async def set_page_mode(self, id, enabled):
        await self.col.update_one({"id": id}, {"$set": {"page_mode": enabled}})
    
    async def get_page_mode(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("page_mode", False) if user else False
    
    async def set_page_shortlink(self, id, shortlink_num, url, api):
        key = f"page_shortlinks.shortlink{shortlink_num}"
        await self.col.update_one(
            {"id": id}, 
            {"$set": {f"{key}.url": url, f"{key}.api": api}}
        )
    
    async def get_page_shortlinks(self, id):
        user = await self.col.find_one({"id": int(id)})
        if user:
            return user.get("page_shortlinks", {
                "shortlink1": {"url": None, "api": None},
                "shortlink2": {"url": None, "api": None},
                "shortlink3": {"url": None, "api": None}
            })
        return {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        }
    
    async def remove_page_shortlink(self, id, shortlink_num):
        key = f"page_shortlinks.shortlink{shortlink_num}"
        await self.col.update_one(
            {"id": id}, 
            {"$set": {f"{key}.url": None, f"{key}.api": None}}
        )

    async def get_page_code(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("page_code") if user else None
    
    async def regenerate_page_code(self, id):
        import secrets
        new_page_code = secrets.token_urlsafe(8)
        await self.col.update_one({"id": id}, {"$set": {"page_code": new_page_code}})
        return new_page_code
    
    async def get_user_by_page_code(self, page_code):
        return await self.col.find_one({"page_code": page_code})

    # --------------------------- Storage Bot Users ----------------------------

    def snew_user(self, id):
        return dict(
            id=id,
            join_date=datetime.date.today().isoformat(),
        )

    async def sadd_user(self, id):
        user = self.snew_user(id)
        await self.su.insert_one(user)

    async def sget_user(self, id):
        return await self.su.find_one({"id": id})

    async def sis_user_exist(self, id):
        user = await self.su.find_one({"id": int(id)})
        return bool(user)

    async def stotal_users_count(self):
        return await self.su.count_documents({})

    async def sget_all_users(self):
        return self.su.find({})

    async def sdelete_user(self, user_id):
        await self.su.delete_many({"id": int(user_id)})


    # --------------------------- Warn Bot Users ----------------------------

    def wnew_user(self, id : int, msg : str =None):
        return dict(
            id=int(id),
            warn_count= 1,
            warn_msg=str(msg),
            warn_date=datetime.date.today().isoformat(),
        )
    
    async def wadd_user(self, id : int, msg : str):
        user = self.wnew_user(id, msg)
        await self.warn.insert_one(user)

    async def wget_user(self, id : int):
        return await self.warn.find_one({"id": id})
    
    async def is_wuser_exist(self, id : int):
        user = await self.warn.find_one({"id": int(id)})
        return bool(user)
    
    async def wupdate_user(self, id : int, msg : str, count : int):
        await self.warn.update_one({"id": id}, {"$set": {"warn_msg": msg, "warn_count": count}})
    
    async def wtotal_users_count(self):
        return await self.warn.count_documents({})
    
    async def wget_all_users(self):
        return self.warn.find({})
    
    async def wdelete_user(self, user_id):
        await self.warn.delete_many({"id": int(user_id)})

    # --------------------------- Inactive Bot Users ----------------------------

    def inew_user(self, id):
        return dict(
            id=id,
            join_date=datetime.date.today().isoformat(),
        )
    
    async def iadd_user(self, id):
        user = self.inew_user(id)
        await self.Inactive.insert_one(user)

    async def iget_user(self, id):
        return await self.Inactive.find_one({"id": id})
    
    async def iis_user_exist(self, id):
        user = await self.Inactive.find_one({"id": int(id)})
        return bool(user)
    
    async def itotal_users_count(self):
        return await self.Inactive.count_documents({})

    async def add_pending_file(self, id, file_data):
        await self.col.update_one({"id": id}, {"$push": {"pending_files": file_data}})

    async def get_pending_files(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("pending_files", [])

    async def clear_pending_files(self, id):
        await self.col.update_one({"id": id}, {"$set": {"pending_files": []}})

    async def remove_pending_file(self, id, file_index):
        user = await self.col.find_one({"id": int(id)})
        files = user.get("pending_files", [])
        if 0 <= file_index < len(files):
            files.pop(file_index)
            await self.col.update_one({"id": id}, {"$set": {"pending_files": files}})

    # User state methods for handling multi-step operations
    async def set_user_state(self, id, state):
        await self.col.update_one({"id": id}, {"$set": {"user_state": state}})

    async def get_user_state(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("user_state", None)

    # Verify functionality methods
    async def set_verify_mode(self, id, enabled):
        await self.col.update_one({"id": id}, {"$set": {"verify_mode": enabled}})
    
    async def get_verify_mode(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("verify_mode", False) if user else False
    
    async def set_verify_shortlink(self, id, shortlink_num, url, api):
        key = f"verify_shortlinks.shortlink{shortlink_num}"
        await self.col.update_one(
            {"id": id}, 
            {"$set": {f"{key}.url": url, f"{key}.api": api}}
        )
    
    async def get_verify_shortlinks(self, id):
        user = await self.col.find_one({"id": int(id)})
        if user:
            return user.get("verify_shortlinks", {
                "shortlink1": {"url": None, "api": None},
                "shortlink2": {"url": None, "api": None},
                "shortlink3": {"url": None, "api": None}
            })
        return {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        }
    
    async def remove_verify_shortlink(self, id, shortlink_num):
        key = f"verify_shortlinks.shortlink{shortlink_num}"
        await self.col.update_one(
            {"id": id}, 
            {"$set": {f"{key}.url": None, f"{key}.api": None}}
        )
    
    async def set_verify_time_gap(self, id, time_gap):
        await self.col.update_one({"id": id}, {"$set": {"verify_time_gap": time_gap}})
    
    async def get_verify_time_gap(self, id):
        user = await self.col.find_one({"id": int(id)})
        return user.get("verify_time_gap", 14400) if user else 14400
    
    async def get_verification_status(self, id):
        user = await self.col.find_one({"id": int(id)})
        if user:
            return user.get("verification_status", {
                "last_verified": None,
                "second_verified": None, 
                "third_verified": None,
                "verify_count_today": 0,
                "last_reset_date": None
            })
        return {
            "last_verified": None,
            "second_verified": None,
            "third_verified": None,
            "verify_count_today": 0,
            "last_reset_date": None
        }
    
    async def update_verification_status(self, id, status_update):
        await self.col.update_one(
            {"id": id}, 
            {"$set": {f"verification_status.{k}": v for k, v in status_update.items()}}
        )
    
    async def is_user_verified_today(self, id):
        """Check if user has completed any verification today"""
        import datetime
        verification_status = await self.get_verification_status(id)
        today = datetime.date.today().isoformat()
        
        # Check if user verified today
        last_verified = verification_status.get("last_verified")
        if last_verified and isinstance(last_verified, str) and last_verified.startswith(today):
            return True
        return False
    
    async def get_verify_shortlink_to_use(self, id):
        """Determine which verify shortlink should be used based on verification count"""
        verification_status = await self.get_verification_status(id)
        verify_shortlinks = await self.get_verify_shortlinks(id)
        
        # Count how many verifications done today
        verify_count = verification_status.get("verify_count_today", 0)
        
        # Logic: Start with shortlink3, then shortlink2, then shortlink1, then direct
        if verify_count == 0:
            # First verification - use shortlink3 if available
            if verify_shortlinks["shortlink3"]["url"] and verify_shortlinks["shortlink3"]["api"]:
                return "shortlink3", verify_shortlinks["shortlink3"]
        elif verify_count == 1:
            # Second verification - use shortlink2 if available
            if verify_shortlinks["shortlink2"]["url"] and verify_shortlinks["shortlink2"]["api"]:
                return "shortlink2", verify_shortlinks["shortlink2"]
        elif verify_count == 2:
            # Third verification - use shortlink1 if available
            if verify_shortlinks["shortlink1"]["url"] and verify_shortlinks["shortlink1"]["api"]:
                return "shortlink1", verify_shortlinks["shortlink1"]
        
        # If we've done 3+ verifications or no shortlinks configured, go direct
        return "direct", None
    
    async def increment_verify_count(self, id):
        """Increment verification count for today"""
        import datetime
        today = datetime.date.today().isoformat()
        verification_status = await self.get_verification_status(id)
        
        # Reset count if it's a new day
        if verification_status.get("last_reset_date") != today:
            await self.update_verification_status(id, {
                "verify_count_today": 1,
                "last_reset_date": today
            })
        else:
            # Increment count
            current_count = verification_status.get("verify_count_today", 0)
            await self.update_verification_status(id, {
                "verify_count_today": current_count + 1
            })
    
    async def mark_user_verified(self, id, verification_type="last"):
        """Mark user as verified with timestamp"""
        import datetime
        now = datetime.datetime.now().isoformat()
        
        # Update verification timestamp
        await self.update_verification_status(id, {
            f"{verification_type}_verified": now
        })
        
        # Increment verification count
        await self.increment_verify_count(id)

    # Page settings methods for users
    async def get_page_settings(self, id):
        """Get page mode customization settings for user"""
        user = await self.col.find_one({"id": int(id)})
        if user:
            return user.get("page_settings", {
                "shortlink_tutorials": {
                    "shortlink1": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"},
                    "shortlink2": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"},
                    "shortlink3": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"}
                },
                "button_visibility": {
                    "watch": True,
                    "download": True,
                    "telegram": True
                },
                "button_names": {
                    "watch": "🎮 Watch Online",
                    "download": "📥 Download",
                    "telegram": "📱 Telegram Storage"
                },
                "custom_buttons": []
            })
        return {
            "shortlink_tutorials": {
                "shortlink1": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"},
                "shortlink2": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"},
                "shortlink3": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"}
            },
            "button_visibility": {
                "watch": True,
                "download": True,
                "telegram": True
            },
            "button_names": {
                "watch": "🎮 Watch Online",
                "download": "📥 Download",
                "telegram": "📱 Telegram Storage"
            },
            "custom_buttons": []
        }
    
    async def update_page_settings(self, id, page_settings):
        """Update page mode customization settings for user"""
        await self.col.update_one({"id": id}, {"$set": {"page_settings": page_settings}})
    
    async def get_verify_settings(self, id):
        """Get verify mode customization settings for user"""
        user = await self.col.find_one({"id": int(id)})
        if user:
            return user.get("verify_settings", {
                "shortlink_tutorials": {
                    "shortlink1": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                    "shortlink2": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                    "shortlink3": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"}
                }
            })
        return {
            "shortlink_tutorials": {
                "shortlink1": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                "shortlink2": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                "shortlink3": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"}
            }
        }
    
    async def update_verify_settings(self, id, verify_settings):
        """Update verify mode customization settings for user"""
        await self.col.update_one({"id": id}, {"$set": {"verify_settings": verify_settings}})
    
    # Page settings methods for channels
    async def get_chl_page_settings(self, chat_id):
        """Get page mode customization settings for channel"""
        chat = await self.chl.find_one({"chat_id": int(chat_id)})
        if chat and chat.get("settings"):
            return chat["settings"].get("page_settings", {
                "shortlink_tutorials": {
                    "shortlink1": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"},
                    "shortlink2": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"},
                    "shortlink3": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"}
                },
                "button_visibility": {
                    "watch": True,
                    "download": True,
                    "telegram": True
                },
                "button_names": {
                    "watch": "🎮 Watch Online",
                    "download": "📥 Download",
                    "telegram": "📱 Telegram Storage"
                },
                "custom_buttons": []
            })
        return {
            "shortlink_tutorials": {
                "shortlink1": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"},
                "shortlink2": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"},
                "shortlink3": {"enabled": False, "video_url": None, "button_text": "📺 Tutorial"}
            },
            "button_visibility": {
                "watch": True,
                "download": True,
                "telegram": True
            },
            "button_names": {
                "watch": "🎮 Watch Online",
                "download": "📥 Download",
                "telegram": "📱 Telegram Storage"
            },
            "custom_buttons": []
        }
    
    async def update_chl_page_settings(self, chat_id, page_settings):
        """Update page mode customization settings for channel"""
        await self.chl.update_one(
            {"chat_id": int(chat_id)}, 
            {"$set": {"settings.page_settings": page_settings}}
        )
    
    async def get_chl_verify_settings(self, chat_id):
        """Get verify mode customization settings for channel"""
        chat = await self.chl.find_one({"chat_id": int(chat_id)})
        if chat and chat.get("settings"):
            return chat["settings"].get("verify_settings", {
                "shortlink_tutorials": {
                    "shortlink1": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                    "shortlink2": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                    "shortlink3": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"}
                }
            })
        return {
            "shortlink_tutorials": {
                "shortlink1": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                "shortlink2": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"},
                "shortlink3": {"enabled": False, "video_url": None, "button_text": "📺 Verify Tutorial"}
            }
        }
    
    async def update_chl_verify_settings(self, chat_id, verify_settings):
        """Update verify mode customization settings for channel"""
        await self.chl.update_one(
            {"chat_id": int(chat_id)}, 
            {"$set": {"settings.verify_settings": verify_settings}}
        )

    # Channel verify shortlinks methods
    async def set_chl_verify_mode(self, chat_id, enabled):
        """Set verify mode for channel"""
        await self.chl.update_one(
            {"chat_id": int(chat_id)}, 
            {"$set": {"settings.verify_mode": enabled}}
        )
    
    async def get_chl_verify_mode(self, chat_id):
        """Get verify mode status for channel"""
        chat = await self.chl.find_one({"chat_id": int(chat_id)})
        if chat and chat.get("settings"):
            return chat["settings"].get("verify_mode", False)
        return False
    
    async def set_chl_verify_shortlink(self, chat_id, shortlink_num, url, api):
        """Set verify shortlink for channel"""
        key = f"settings.verify_shortlinks.shortlink{shortlink_num}"
        await self.chl.update_one(
            {"chat_id": int(chat_id)}, 
            {"$set": {f"{key}.url": url, f"{key}.api": api}}
        )
    
    async def get_chl_verify_shortlinks(self, chat_id):
        """Get verify shortlinks for channel"""
        chat = await self.chl.find_one({"chat_id": int(chat_id)})
        if chat and chat.get("settings") and chat["settings"].get("verify_shortlinks"):
            return chat["settings"]["verify_shortlinks"]
        return {
            "shortlink1": {"url": None, "api": None},
            "shortlink2": {"url": None, "api": None},
            "shortlink3": {"url": None, "api": None}
        }
    
    async def remove_chl_verify_shortlink(self, chat_id, shortlink_num):
        """Remove verify shortlink for channel"""
        key = f"settings.verify_shortlinks.shortlink{shortlink_num}"
        await self.chl.update_one(
            {"chat_id": int(chat_id)}, 
            {"$set": {f"{key}.url": None, f"{key}.api": None}}
        )
    
    async def set_chl_verify_time_gap(self, chat_id, time_gap):
        """Set verify time gap for channel"""
        await self.chl.update_one(
            {"chat_id": int(chat_id)}, 
            {"$set": {"settings.verify_time_gap": time_gap}}
        )
    
    async def get_chl_verify_time_gap(self, chat_id):
        """Get verify time gap for channel"""
        chat = await self.chl.find_one({"chat_id": int(chat_id)})
        if chat and chat.get("settings"):
            return chat["settings"].get("verify_time_gap", 14400)
        return 14400


# Initialize database instance
from MrAKTech.config import Telegram

u_db = Database(Telegram.DATABASE_URL, Telegram.DATABASE_NAME)
