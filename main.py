from asyncio import sleep
from contextlib import suppress
from gc import collect
from os import environ
from re import findall

from pyrogram import Client, idle
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import FloodWait, RPCError, UserAlreadyParticipant
from pyrogram.filters import channel, command, photo, private, text, user
from pyrogram.types import Message
from redis.asyncio import Redis

TOKEN = environ.get("TOKEN", "6844752791:AAHxfSChzlt22hiKBYs0x3Q-hgQBk2_PZ64")
STRING = environ.get(
    "STRING",
    "BQGxY4UAH2vMpBlVlPhi0I4JRNdkdDo0BoQXZH5iMDMC7KiKC0Nq9FF3zZ5JSor8MJBtzEdU06JRVzZZLqcBRVYWgIn34elZouk2EpdI8gT9VDaQae_LjFhwZka9hmjUGDQUPqdMKGnDe_bodAy2IohRc8x4-9ba2co9hsTUIEDYY707eSHJV01aHOZ1QkKLMjuymkq-4EniGaxb1YHBY9s9EaEmVhrpQPS2YcSWNFdCfcsD2OMXqSBmGYtzUmORNQpqvYaygDBV4S4_7Wl3XYuaez3miATsTzGZ8tbWrhIdLWWPv4ebMpDo5IL8moTM6fFNICKEeg5MmCNJf7j535nA5-qCQgAAAABvO-26AA",
)
API_ID = int(environ.get("API_ID", 28402565))
API_HASH = environ.get("API_HASH", "fd3d8a3da43239bbfd0c2b3e048a4e47")
REDISDBURL = environ.get(
    "DB_URL",
    "redis://default:BpDwFaKcdJqK1FxywB8JrOFw1B1X0C0K@redis-19798.c91.us-east-1-3.ec2.cloud.redislabs.com:19798",
)
USEB = int(environ.get("ADMIN", 5446536405))
USERS = [USEB, 1594433798, 6022301649]
pbot = Client("forwardbot", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)
ubot = Client("forwarder", api_id=API_ID, api_hash=API_HASH, session_string=STRING)
REDIS = Redis.from_url(REDISDBURL, decode_responses=True)
try:
    pbot.loop.run_until_complete(REDIS.ping())
except Exception:
    exit("Unable to connect with redisdb !")


async def replaceshits(tex: str):
    for i in findall(r"(@[A-Za-z0-9_]*[A-Za-z]+[A-Za-z0-9_]*( |$|\b))", tex):
        tex = tex.replace(i[0], "")
    for i in findall(
        r"((http(s)?://)?(t|telegram)\.(me|dog)/[A-Za-z0-9_]+( |$|\b))", tex
    ):
        tex = tex.replace(i[0], "")
    for x in await REDIS.smembers("words"):
        tex = tex.replace(x, "")
    return tex


@pbot.on_message(command("start") & private)
async def startb(_, m: Message):
    await m.reply_text("I'm alive!\nCustom forwarder bot Made by @annihilatorrrr !")
    return


@pbot.on_message(command("addchannel") & private & user(USERS))
async def addchannel(c: Client, m: Message):
    args = m.command[1:]
    if len(args) >= 2:
        try:
            source = await c.get_chat(args[0])
        except RPCError as e:
            await m.reply_text(
                f"Error: {e.MESSAGE}; I don't know that channel yet, so try with username or just forward me a message from source channel and try again this command!"
            )
            return
        if source.type != ChatType.CHANNEL:
            await m.reply_text("Chat is not a channel!")
            return
        with suppress(UserAlreadyParticipant):
            await ubot.join_chat(source.id)
        try:
            desti = await c.get_chat(args[1])
        except RPCError as e:
            await m.reply_text(e.MESSAGE)
            return
        with suppress(UserAlreadyParticipant):
            await ubot.join_chat(desti.id)
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


@pbot.on_message(command("rmchannel") & private & user(USERS))
async def rmchannel(c: Client, m: Message):
    args = m.command[1:]
    if len(args) >= 1:
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


@pbot.on_message(command("channels") & private & user(USERS))
async def channels(_: Client, m: Message):
    x = "Channels:\n"
    for a in await REDIS.keys("-100*"):
        x += f"> {a}: {await REDIS.get(a)}\n"
    await m.reply_text(x)
    return


@pbot.on_message(command("words") & private & user(USERS))
async def words(_: Client, m: Message):
    x = "Words to be removed:\n"
    for a in await REDIS.smembers("words"):
        x += f"> {a}\n"
    await m.reply_text(x)
    return


@pbot.on_message(command("addword") & private & user(USERS))
async def addword(_: Client, m: Message):
    args = m.command[1:]
    if len(args) >= 1:
        await REDIS.sadd("words", *args)
        await m.reply_text("Added!")
    else:
        await m.reply_text("Provide some words to add!")
    return


@pbot.on_message(command("rmword") & private & user(USERS))
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
        capt = (
            await replaceshits(m.caption.html)
            if m.caption
            else await replaceshits(m.text.html)
            if m.text
            else None
        )
        try:
            if m.text:
                if not capt:
                    return
                try:
                    await ubot.send_message(
                        int(data),
                        capt,
                        ParseMode.HTML,
                        disable_web_page_preview=not m.web_page,
                    )
                except FloodWait as e:
                    await sleep(e.value + 1)
                    await ubot.send_message(
                        int(data),
                        capt,
                        ParseMode.HTML,
                        disable_web_page_preview=not m.web_page,
                    )
            else:
                try:
                    await m.copy(int(data), caption=capt)
                except FloodWait as fe:
                    await sleep(fe.value + 1)
                    await m.copy(int(data), caption=capt)
        except Exception:
            return
    return


@ubot.on_message(channel & photo | text, group=2)
async def forward(c: Client, m: Message):
    c.loop.create_task(worker(m))
    collect()
    return


pbot.start()
ubot.start()
print("Started!")
idle()
ubot.stop(True)
pbot.stop(True)
print("Bye!")
