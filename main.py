import os
import asyncio
import yt_dlp

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped

# ============================================
# CONFIG
# ============================================

API_ID = int(os.environ.get("API_ID", "38680007"))
API_HASH = os.environ.get("API_HASH", "cc233beb120c0bd019b2e295d07cb31b")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8735943404:AAGXitz_yEDs7SaIK4a2FxFs2B9-BNlq-S4")
SESSION_STRING = os.environ.get("BQJONccAV7uSh7ndaODzh5n0DY6Z6-0FR3HpEpBV8hmZHAU_fTAT6FYx-PWDsd9B5905B1ZE05eIi-4-8TyXvxdKI4pI0LuBINxZoFWvtfZUl_kGevn7unH_CpRIEgyc7gMLMygNLAQyXmm7ZNoljwouDoCdWYwsG0LgNdc97QpLpabvTCAHas5Go-oFtBBRX9qMB9TJ8-tZGhouE2lOoAPMTFPML025Sv7nnO1IFDnIUFcUt9RZjpxpAbgIegsE0s7543sraAdkXGdlHRS2qGGD6apQceR2EehOj9erzAMF0bvcaSAXF9dzM6idflSu_795bRRlROQ7XG2kurpCsV_x5iB8MgAAAAIWYXuSAA", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "8965421970")

# ============================================
# CLIENTS
# ============================================

bot = Client(
    "music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

assistant = Client(
    "assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
)

call = PyTgCalls(assistant)

# ============================================
# QUEUE
# ============================================

queues = {}

def get_queue(chat_id):
    if chat_id not in queues:
        queues[chat_id] = []
    return queues[chat_id]

# ============================================
# YOUTUBE SEARCH
# ============================================

def youtube_search(query):
    options = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "default_search": "ytsearch",
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        data = ydl.extract_info(f"ytsearch1:{query}", download=False)

    if not data or not data.get("entries"):
        return None

    video = data["entries"][0]
    vid_id = video.get("id")
    url = video.get("url") or f"https://www.youtube.com/watch?v={vid_id}"
    if not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={vid_id}"

    return {
        "title": video.get("title", "Unknown"),
        "webpage_url": url,
        "duration": video.get("duration") or 0,
    }

def get_audio(url):
    options = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
        return info["url"]

# ============================================
# COMMANDS
# ============================================

@bot.on_message(filters.command("start"))
async def start(_, message):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🎵 Help", callback_data="help")]])
    await message.reply_text(
        "🎵 **Music Bot Online!**\n\n"
        "Use: `/play song name`\n\n"
        "Bot ko group me admin banao aur voice chat start karo.",
        reply_markup=kb,
    )

@bot.on_message(filters.command("help"))
async def help_command(_, message):
    await message.reply_text(
        "🎵 **Commands**\n\n"
        "▶️ `/play song`\n"
        "⏸️ `/pause`\n"
        "▶️ `/resume`\n"
        "⏭️ `/skip`\n"
        "⏹️ `/stop`\n"
        "📋 `/queue`\n"
        "ℹ️ `/current`\n"
        "🏓 `/ping`"
    )

@bot.on_message(filters.command("play"))
async def play(_, message):
    if len(message.command) < 2:
        return await message.reply_text("❌ `/play song name`")

    query = " ".join(message.command[1:])
    status = await message.reply_text("🔎 Searching...")

    try:
        result = await asyncio.to_thread(youtube_search, query)
        if not result:
            return await status.edit_text("❌ Song nahi mila.")

        chat_id = message.chat.id
        queue = get_queue(chat_id)
        queue.append(result)

        if len(queue) == 1:
            audio_url = await asyncio.to_thread(get_audio, result["webpage_url"])
            try:
                await call.play(chat_id, AudioPiped(audio_url))
            except Exception:
                await call.change_stream(chat_id, AudioPiped(audio_url))

            await status.edit_text(f"🎵 **Now Playing**\n\n🎶 {result['title']}")
        else:
            await status.edit_text(
                f"✅ **Added to Queue**\n\n🎶 {result['title']}\n📋 Position: {len(queue)}"
            )

    except Exception as e:
        await status.edit_text(f"❌ Error:\n`{str(e)[:400]}`")

@bot.on_message(filters.command("queue"))
async def queue_command(_, message):
    q = get_queue(message.chat.id)
    if not q:
        return await message.reply_text("📋 Queue empty.")
    text = "📋 **Music Queue**\n\n" + "\n".join(
        f"{i}. 🎵 {s['title']}" for i, s in enumerate(q, 1)
    )
    await message.reply_text(text)

@bot.on_message(filters.command("current"))
async def current(_, message):
    q = get_queue(message.chat.id)
    if not q:
        return await message.reply_text("❌ Nothing playing.")
    await message.reply_text(f"🎵 **Currently Playing**\n\n🎶 {q[0]['title']}")

@bot.on_message(filters.command("pause"))
async def pause(_, message):
    try:
        await call.pause(message.chat.id)
        await message.reply_text("⏸️ Paused.")
    except Exception as e:
        await message.reply_text(f"❌ `{str(e)[:200]}`")

@bot.on_message(filters.command("resume"))
async def resume(_, message):
    try:
        await call.resume(message.chat.id)
        await message.reply_text("▶️ Resumed.")
    except Exception as e:
        await message.reply_text(f"❌ `{str(e)[:200]}`")

@bot.on_message(filters.command("stop"))
async def stop(_, message):
    chat_id = message.chat.id
    try:
        await call.leave_call(chat_id)
    except Exception:
        pass
    queues.pop(chat_id, None)
    await message.reply_text("⏹️ Stopped & queue cleared.")

@bot.on_message(filters.command("skip"))
async def skip(_, message):
    chat_id = message.chat.id
    q = get_queue(chat_id)

    if not q:
        return await message.reply_text("❌ Queue empty.")

    q.pop(0)

    if not q:
        try:
            await call.leave_call(chat_id)
        except Exception:
            pass
        return await message.reply_text("⏭️ Queue finished.")

    nxt = q[0]
    try:
        audio_url = await asyncio.to_thread(get_audio, nxt["webpage_url"])
        await call.change_stream(chat_id, AudioPiped(audio_url))
        await message.reply_text(f"⏭️ **Next**\n\n🎶 {nxt['title']}")
    except Exception as e:
        await message.reply_text(f"❌ `{str(e)[:300]}`")

@bot.on_callback_query()
async def callbacks(_, query):
    if query.data == "help":
        await query.answer()
        await query.message.edit_text("🎵 `/play /pause /resume /skip /stop /queue /current`")

@bot.on_message(filters.command("ping"))
async def ping(_, message):
    await message.reply_text("🏓 **PONG!** Bot online.")

# ============================================
# RUN
# ============================================

async def main():
    await bot.start()
    await assistant.start()
    await call.start()
    print("🎵 MUSIC BOT STARTED")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

