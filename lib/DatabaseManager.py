import time
from asyncio import AbstractEventLoop

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.collection import Collection


class DatabaseManager:
    def __init__(self, mongo_uri: str, database_name: str, loop: AbstractEventLoop):
        self.client = AsyncIOMotorClient(mongo_uri, io_loop=loop)
        self.db = self.client[database_name]

    async def get_pack(
        self,
        pack_id: str,
    ):
        coll: Collection = self.db["packs"]
        pack = await coll.find_one({"pack_id": pack_id})

        return pack

    async def get_pack_from_name(self, name: str):
        coll: Collection = self.db["packs"]
        pack = await coll.find_one({"name": name})

        return not not pack

    async def get_creator(
        self,
        pack_id: str,
    ):
        coll: Collection = self.db["packs"]
        pack = await coll.find_one({"pack_id": pack_id})

        if not pack:
            return None

        return pack["creator"]

    async def create_pack(self, user_id: str, name: str, tray: str, message_id: int):
        pack_id = hex(message_id).replace("0x", "")

        coll: Collection = self.db["packs"]
        await coll.insert_one(
            {
                "name": name,
                "creator": user_id,
                "pack_id": pack_id,
                "animated": False,
                "tray_image": tray,
                "image_data_version": 0,
                "created_at": int(time.time()),
                "data": [],
            }
        )

        return pack_id

    async def add_emote(
        self,
        pack_id: str,
        creator: str,
        emote_url: str,
        emote_name: str,
        emote_id: str,
        is_animated: str,
    ):
        coll: Collection = self.db["packs"]
        pack = await coll.find_one({"pack_id": pack_id, "creator": creator})

        if not pack:
            return None

        await coll.update_one(
            {"pack_id": pack_id, "creator": creator},
            {
                "$push": {
                    "data": {
                        "url": emote_url,
                        "name": emote_name,
                        "id": emote_id,
                        "animated": is_animated,
                    }
                },
                "$inc": {
                    "image_data_version": 1
                }
            },
        )

        if not pack["animated"] and is_animated:
            await coll.update_one(
                {"pack_id": pack_id, "creator": creator}, {"$set": {"animated": True}}
            )

        return True

    async def get_user_packs(self, user_id: str):
        coll: Collection = self.db["packs"]
        result = await coll.find({"creator": user_id}).to_list(length=None)
        return result
