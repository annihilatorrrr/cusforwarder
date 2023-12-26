from asyncio import sleep
from contextlib import suppress
from gc import collect
from os import environ
from re import findall

from uvloop import install

install()
from pyrogram import Client, idle
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import FloodWait, RPCError, UserAlreadyParticipant
from pyrogram.filters import channel, command, photo, private, text, user
from pyrogram.types import Message
from redis.asyncio import Redis

TOKEN = environ.get("TOKEN", "6844752791:AAHxfSChzlt22hiKBYs0x3Q-hgQBk2_PZ64")
STRING = environ.get(
    "STRING",
    "BQFmONcAXr-CIDZ6SByz2Ypg0HMmDO_QGAk7jBc8RdXVSEo0KSuygVrxZivM6_1mz2MaBrudv4Y1PpXM2ogj6n94c580B7iOBIhT9mkoLbgNDgH_9XQ3CMZyeDetqXQiKrge6LKLIghotd3JB303X3Ofbw3-Fn9URbm5RQeEeSE1fLLSLnCSyX3DNfewi6_djZQAANhhibpiTUdin-gY7MebritkV72FIZaKrXn9qLf8Ebm6R7OOaLA26qyikk-AUXdZhAtjq2qK89gRg7_WtcMz_P00wRMeN1lsJPkf0Mld3lX6tccnNbc3YnoQq0UemyCP-gpPKdUwKrG2cjEW0UdQcET0IQAAAAF6OR8uAA",
)
API_ID = int(environ.get("API_ID", 23476439))
API_HASH = environ.get("API_HASH", "1626e884119a29dbccbb78e39b48128f")
REDISDBURL = environ.get(
    "DB_URL",
    "redis://default:BpDwFaKcdJqK1FxywB8JrOFw1B1X0C0K@redis-19798.c91.us-east-1-3.ec2.cloud.redislabs.com:19798",
)
USEB = int(environ.get("ADMIN", 5446536405))
USERS = [USEB, 1594433798, 6022301649, 1733251099]
pbot = Client("forwardbot", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)
ubot = Client("forwarder",
              api_id=API_ID,
              api_hash=API_HASH,
              session_string=STRING)
REDIS = Redis.from_url(REDISDBURL, decode_responses=True)
try:
    pbot.loop.run_until_complete(REDIS.ping())
except Exception:
    exit("Unable to connect with redisdb !")


async def replaceshits(tex: str):
    for i in findall(r"(@[A-Za-z0-9_]*[A-Za-z]+[A-Za-z0-9_]*( |$|\b))", tex):
        tex = tex.replace(i[0], "")
    for i in findall(
            r"((http(s)?://)?(t|telegram)\.(me|dog)/[A-Za-z0-9_]+( |$|\b))",
            tex):
        tex = tex.replace(i[0], "")
    for x in await REDIS.smembers("words"):
        tex = tex.replace(x, "")
    return tex


@pbot.on_message(command("start") & private)
async def startb(_, m: Message):
    await m.reply_text(
        "I'm alive!\nCustom forwarder bot Made by @annihilatorrrr !")
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
        await m.reply_text(
            "Provide like: /addchannel sourcechatid destinationchatid")
    return


@pbot.on_message(command("rmchannel") & private & user(USERS))
async def rmchannel(c: Client, m: Message):
    args = m.command[1:]
    if len(args) >= 1:
        try:
            source = await c.get_chat(args[0])
            args[0] = source.id
        except RPCError:
            if not args[0].startswith("-100"):
                await m.reply_text("Please provide the channel id")
                return
        await REDIS.delete(args[0])
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
        capt = (await replaceshits(m.caption.html) if m.caption else
                await replaceshits(m.text.html) if m.text else None)
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
    await worker(m)
    collect()
    return


pbot.start()
ubot.start()
print("Started!")
idle()
ubot.stop(True)
pbot.stop(True)
print("Bye!")
