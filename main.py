from asyncio import sleep
from gc import collect
from os import environ
from re import findall

from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.errors import FloodWait, RPCError
from pyrogram.filters import channel, command, private, user
from pyrogram.types import Message
from redis.asyncio import Redis

TOKEN = environ.get("TOKEN", "")
STRING = environ.get("STRING", "")
API_ID = int(environ.get("API_ID", 0))
API_HASH = environ.get("API_HASH", "")
REDISDBURL = environ.get("DB_URL", "")
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
    for i in findall(
        r"((http(s)?://)?(t|telegram)\.(me|dog)/[A-Za-z0-9_]+( |$|\b))", text
    ):
        text = text.replace(i[0], "")
    for x in await REDIS.smembers("words"):
        text = text.replace(x, "")
    return text


@pbot.on_message(command("start") & private)
async def startb(_, m: Message):
    await m.reply_text("I'm alive!\nCustom forwarder bot Made by @annihilatorrrr !")
    return


@pbot.on_message(command("addchannel") & private & user(6022301649))
async def addchannel(c: Client, m: Message):
    args = m.command[1:]
    if len(args) >= 2:
        try:
            source = await c.get_chat(args[0])
        except RPCError as e:
            await m.reply_text(e.MESSAGE)
            return
        if source.type != ChatType.CHANNEL:
            await m.reply_text("Chat is not a channel!")
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
        try:
            ub = await c.get_chat_member(desti.id, c.me.id)
            if not ub.privileges.can_post_messages:
                await m.reply_text(
                    "I need: post message, promote members permission in the destination channel!"
                )
                return
            await c.promote_chat_member(desti.id, ubot.me.id, ub.privileges)
        except:
            pass
        await REDIS.set(source.id, desti.id)
        await m.reply_text("Added!")
    else:
        await m.reply_text("Provide like: /addchannel sourcechatid destinationchatid")
    return


@pbot.on_message(command("rmchannel") & private & user(6022301649))
async def rmchannel(c: Client, m: Message):
    args = m.command[1:]
    if len(args) >= 2:
        try:
            source = await c.get_chat(args[0])
        except RPCError as e:
            await m.reply_text(e.MESSAGE)
            return
        await REDIS.delete(source.id)
        await m.reply_text("Remove!")
    else:
        await m.reply_text("Provide like: /rmchannel sourcechatid")
    return


@pbot.on_message(command("channels") & private & user(6022301649))
async def channels(_: Client, m: Message):
    x = "Channels:\n"
    for a in await REDIS.keys("-100"):
        x += f"{a} - {await REDIS.get(a)}\n"
    await m.reply_text(x)
    return


@pbot.on_message(command("words") & private & user(6022301649))
async def words(_: Client, m: Message):
    x = "Words to be removed:\n"
    for a in await REDIS.smembers("words"):
        x += f"{a}\n"
    await m.reply_text(x)
    return


@pbot.on_message(command("addword") & private & user(6022301649))
async def addword(_: Client, m: Message):
    args = m.command[1:]
    if len(args) >= 1:
        await REDIS.sadd("words", *args)
        await m.reply_text("Added!")
    else:
        await m.reply_text("Provide some words to add!")
    return


@pbot.on_message(command("rmword") & private & user(6022301649))
async def rmword(_: Client, m: Message):
    args = m.command[1:]
    if len(args) >= 1:
        await REDIS.srem("words", *args)
        await m.reply_text("Removed!")
    else:
        await m.reply_text("Provide some words to remove!")
    return


async def worker(m: Message):
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
    c.loop.create_task(worker(m))
    collect()
    return


pbot.start()
print("Started!")
ubot.run()
pbot.stop(True)
print("Bye!")
