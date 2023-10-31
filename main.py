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


async def replaceshits(text: str):
    for i in findall(r"(@[A-Za-z0-9_]+( |$|\b))", text):
        text = text.replace(i[0], "")
    for i in findall(r"((http(s)?://)?(t|telegram)\.(me|dog)/[A-Za-z0-9_]+( |$|\b))", text):
        text = text.replace(i[0], "")
    for x in await REDIS.smembers("words"):
        text = text.replace(x, "")
    return text


@pbot.on_message(command("start") & private)
async def startb(_, m: Message):
    await m.reply_text("I'm alive!\nCustom forwarder bot Made by @annihilatorrrr !")
    return


@pbot.on_message(command("addchannel") & private)
async def addchannel(_, m: Message):
    args = m.command[1:]
    if len(args) >= 2:
        try:
            source = await c.get_chat(args[0])
        except RPCError as e:
            await m.reply_text(e.MESSAGE)
            return
        try:
            desti = await c.get_chat(args[1])
        except RPCError as e:
            await m.reply_text(e.MESSAGE)
            return
        try:
            await ubot.join_chat(desti.invite_link)
        except:
            pass
    else:
        await m.reply_text("Provide like: /addchannel sourcechatid destinationchatid")
    return



async def worker(c: ubot, m: Message):
    if data := await REDIS.get(m.chat.id):
        capt = await replaceshits(m.caption.html) if m.caption else None
        try:
            await m.copy(int(data), caption=capt)
        except FloodWait as fe:
            await sleep(fe.value + 1)
            await m.copy(int(data), caption=capt)
        except Exception:
            pass
    return


@ubot.on_message(channel)
async def forward(c: ubot, m: Message):
    c.loop.create_task(worker(c, m))
    return


pbot.start()
print("Started!")
ubot.run()
pbot.stop(True)
print("Bye!")
