from re import findall

from pyrogram import Client
from pyrogram.filters import private, command, channel
from pyrogram.types import Message
from redis.asyncio import Redis

TOKEN = ""
STRING = ""
API_ID = 0
API_HASH = ""
REDISDBURL = ""
pbot = Client("forwardbot", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)
ubot = Client("forwarder", api_id=API_ID, api_hash=API_HASH, session_string=STRING)
REDIS = Redis.from_url(REDISDBURL, decode_responses=True)
try:
    pbot.loop.run_until_complete(REDIS.ping())
except Exception:
    exit("Unable to connect with redisdb !")


def replaceshits(text: str):
    for i in findall(r"(@[A-Za-z0-9_]+( |$|\b))", text):
        text = text.replace(i[0], "")
    for i in findall(r"((http(s)?://)?(t|telegram)\.(me|dog)/[A-Za-z0-9_]+( |$|\b))", text):
        text = text.replace(i[0], "")
    return text


@pbot.on_message(command("start") & private)
async def startb(_, m: Message):
    await m.reply_text("I'm alive!\nCustom forwarder bot Made by @annihilatorrrr !")
    return


@ubot.on_message(channel)
async def forward(c: ubot, m: Message):
    await m.reply_text("I'm alive!\nCustom forwarder bot Made by @annihilatorrrr !")
    return


pbot.start()
print("Started!")
ubot.run()
pbot.stop(True)
print("Bye!")
