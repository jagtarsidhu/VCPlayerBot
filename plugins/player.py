#!/usr/bin/env python3
# Copyright (C) @subinps
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from utils import LOGGER
from youtube_search import YoutubeSearch
from contextlib import suppress
from pyrogram.types import Message
from yt_dlp import YoutubeDL
from datetime import datetime
from pyrogram import filters
from config import Config
from PTN import parse
import re
from utils import (
    add_to_db_playlist, 
    clear_db_playlist, 
    delete_messages, 
    download, 
    get_admins, 
    get_duration,
    is_admin, 
    get_buttons, 
    get_link, 
    import_play_list, 
    is_audio, 
    leave_call, 
    play, 
    get_playlist_str, 
    send_playlist, 
    shuffle_playlist, 
    start_stream, 
    stream_from_link, 
    chat_filter,
    c_play
)
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton
    )
from pyrogram.errors import (
    MessageIdInvalid, 
    MessageNotModified,
    UserNotParticipant,
    PeerIdInvalid,
    ChannelInvalid
    )
from pyrogram import (
    Client, 
    filters
    )


admin_filter=filters.create(is_admin) 

@Client.on_message(filters.command(["play", "fplay", f"play@{Config.BOT_USERNAME}", f"fplay@{Config.BOT_USERNAME}"]) & chat_filter)
async def add_to_playlist(_, message: Message):
    with suppress(MessageIdInvalid, MessageNotModified):
        admins = await get_admins(Config.CHAT)
        if Config.ADMIN_ONLY:
            if not (message.from_user is None and message.sender_chat or message.from_user.id in admins):
                k=await message.reply("@jagtarsidhu ko bolo ki muje admin bnao fir kus baat ban sakti hai")
                await delete_messages([message, k])
                return
        type=""
        yturl=""
        ysearch=""
        if message.command[0] == "fplay":
            if not (message.from_user is None and message.sender_chat or message.from_user.id in admins):
                k=await message.reply("keval admins k lie hai")
                await delete_messages([message, k])
                return
        msg = await message.reply_text("⚡️ **Checking recived input..**")
        if message.reply_to_message and message.reply_to_message.video:
            await msg.edit("⚡️ **Checking Telegram Media...**")
            type='video'
            m_video = message.reply_to_message.video       
        elif message.reply_to_message and message.reply_to_message.document:
            await msg.edit("⚡️ **Checking Telegram Media...**")
            m_video = message.reply_to_message.document
            type='video'
            if not "video" in m_video.mime_type:
                return await msg.edit("The given file is invalid")
        elif message.reply_to_message and message.reply_to_message.audio:
            #if not Config.IS_VIDEO:
                #return await message.reply("Play from audio file is available only if Video Mode if turned off.\nUse /settings to configure ypur player.")
            await msg.edit("⚡️ **Checking Telegram Media...**")
            type='audio'
            m_video = message.reply_to_message.audio       
        else:
            if message.reply_to_message and message.reply_to_message.text:
                query=message.reply_to_message.text
            elif " " in message.text:
                text = message.text.split(" ", 1)
                query = text[1]
            else:
                await msg.edit("You Didn't gave me anything to play.Reply to a video or a youtube link or a direct link.")
                await delete_messages([message, msg])
                return
            regex = r"^(?:https?:\/\/)?(?:www\.)?youtu\.?be(?:\.com)?\/?.*(?:watch|embed)?(?:.*v=|v\/|\/)([\w\-_]+)\&?"
            match = re.match(regex,query)
            if match:
                type="youtube"
                yturl=query
            elif query.startswith("http"):
                try:
                    has_audio_ = await is_audio(query)
                except:
                    has_audio_ = False
                    LOGGER.error("Unable to get Audio properties within time.")
                if not has_audio_:
                    await msg.edit("This is an invalid link, provide me a direct link or a youtube link.")
                    await delete_messages([message, msg])
                    return
                try:
                    dur=await get_duration(query)
                except:
                    dur=0
                if dur == 0:
                    await msg.edit("This is a live stream, Use /stream command.")
                    await delete_messages([message, msg])
                    return 
                type="direct"
                url=query
            else:
                type="query"
                ysearch=query
        if not message.from_user is None:
            user=f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
            user_id = message.from_user.id
        else:
            user="Anonymous"
            user_id = "anonymous_admin"
        now = datetime.now()
        nyav = now.strftime("%d-%m-%Y-%H:%M:%S")
        if type in ["video", "audio"]:
            if type == "audio":
                title=m_video.title
                unique = f"{nyav}_{m_video.file_size}_audio"
            else:
                title=m_video.file_name
                unique = f"{nyav}_{m_video.file_size}_video"
            file_id=m_video.file_id
            if Config.PTN:
                ny = parse(title)
                title_ = ny.get("title")
                if title_:
                    title = title_
            data={1:title, 2:file_id, 3:"telegram", 4:user, 5:unique}
            if message.command[0] == "fplay":
                pla = [data] + Config.playlist
                Config.playlist = pla
            else:
                Config.playlist.append(data)
            await add_to_db_playlist(data)        
            await msg.edit("Media added to playlist")
        elif type=="youtube" or type=="query":
            if type=="youtube":
                await msg.edit("⚡️ **Fetching Video From YouTube...**")
                url=yturl
            elif type=="query":
                try:
                    await msg.edit("⚡️ **Fetching Video From YouTube...**")
                    ytquery=ysearch
                    results = YoutubeSearch(ytquery, max_results=1).to_dict()
                    url = f"https://youtube.com{results[0]['url_suffix']}"
                    title = results[0]["title"][:40]
                except Exception as e:
                    await msg.edit(
                        "Song not found.\nTry inline mode.."
                    )
                    LOGGER.error(str(e), exc_info=True)
                    await delete_messages([message, msg])
                    return
            else:
                return
            ydl_opts = {
                "quite": True,
                "geo-bypass": True,
                "nocheckcertificate": True
            }
            ydl = YoutubeDL(ydl_opts)
            try:
                info = ydl.extract_info(url, False)
            except Exception as e:
                LOGGER.error(e, exc_info=True)
                await msg.edit(
                    f"YouTube Download Error ❌\nError:- {e}"
                    )
                LOGGER.error(str(e))
                await delete_messages([message, msg])
                return
            title = info["title"]
            data={1:title, 2:url, 3:"youtube", 4:user, 5:f"{nyav}_{user_id}"}
            if message.command[0] == "fplay":
                pla = [data] + Config.playlist
                Config.playlist = pla
            else:
                Config.playlist.append(data)
            await add_to_db_playlist(data)
            await msg.edit(f"[{title}]({url}) added to playist", disable_web_page_preview=True)
        elif type == "direct":
            data={1:"Music", 2:url, 3:"url", 4:user, 5:f"{nyav}_{user_id}"}
            if message.command[0] == "fplay":
                pla = [data] + Config.playlist
                Config.playlist = pla
            else:
                Config.playlist.append(data)
            await add_to_db_playlist(data)        
            await msg.edit("Link added to playlist")
        if not Config.CALL_STATUS \
            and len(Config.playlist) >= 1:
            await msg.edit("Downloading and Processing...")
            await download(Config.playlist[0], msg)
            await play()
        elif (len(Config.playlist) == 1 and Config.CALL_STATUS):
            await msg.edit("Downloading and Processing...")
            await download(Config.playlist[0], msg)  
            await play()
        elif message.command[0] == "fplay":
            await msg.edit("Downloading and Processing...")
            await download(Config.playlist[0], msg)  
            await play()
        else:
            await send_playlist()  
        await msg.delete()
        pl=await get_playlist_str()
        if message.chat.type == "private":
            await message.reply(pl, reply_markup=await get_buttons() ,disable_web_page_preview=True)       
        elif not Config.LOG_GROUP and message.chat.type == "supergroup":
            if Config.msg.get('playlist') is not None:
                await Config.msg['playlist'].delete()
            Config.msg['playlist']=await message.reply(pl, disable_web_page_preview=True, reply_markup=await get_buttons())    
            await delete_messages([message])  
        for track in Config.playlist[:2]:
            await download(track)


@Client.on_message(filters.command(["leave", f"leave@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def leave_voice_chat(_, m: Message):
    if not Config.CALL_STATUS:        
        k=await m.reply("Not joined any voicechat.")
        await delete_messages([m, k])
        return
    await leave_call()
    k=await m.reply("lo ma jaa rha.")
    await delete_messages([m, k])





@Client.on_message(filters.command(["clearplaylist", f"clearplaylist@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def clear_play_list(client, m: Message):
    if not Config.playlist:
        k = await m.reply("Playlist is empty.")  
        await delete_messages([m, k])
        return
    Config.playlist.clear()
    k=await m.reply_text(f"Playlist Cleared.")
    await clear_db_playlist(all=True)
    if Config.IS_LOOP \
        and not (Config.YPLAY or Config.CPLAY):
        await start_stream()
    else:
        await leave_call()
    await delete_messages([m, k])




@Client.on_message(filters.command(["yplay", f"yplay@{Config.BOT_USERNAME}"]) & admin_filter & chat_filter)
async def yt_play_list(client, m: Message):
    with suppress(MessageIdInvalid, MessageNotModified):
        if m.reply_to_message is not None and m.reply_to_message.document:
            if m.reply_to_message.document.file_name != "YouTube_PlayList.json":
                k=await m.reply("Invalid PlayList file given. Use @GetPlayListBot  or search for a playlist in @DumpPlaylist to get a playlist file.")
                await delete_messages([m, k])
                return
            ytplaylist=await m.reply_to_message.download()
            status=await m.reply("Trying to get details from playlist.")
            n=await import_play_list(ytplaylist)
            if not n:
                await status.edit("Errors Occured while importing playlist.")
                await delete_messages([m, status])
                return
            if Config.SHUFFLE:
                await shuffle_playlist()
            pl=await get_playlist_str()
            if m.chat.type == "private":
                await status.edit(pl, disable_web_page_preview=True, reply_markup=await get_buttons())        
            elif not Config.LOG_GROUP and m.chat.type == "supergroup":
                if Config.msg.get("playlist") is not None:
                    await Config.msg['playlist'].delete()
                Config.msg['playlist']=await status.edit(pl, disable_web_page_preview=True, reply_markup=await get_buttons())
                await delete_messages([m])
            else:
                await delete_messages([m, status])
        else:
            k=await m.reply("No playList file given. Use @GetPlayListBot  or search for a playlist in @DumpPlaylist to get a playlist file.")
            await delete_messages([m, k])



        


admincmds=["yplay", "leave", "pause", "resume", "skip", "restart", "volume", "shuffle", "clearplaylist", "export", "import", "update", 'replay', 'logs', 'stream', 'fplay', 'schedule', 'record', 'slist', 'cancel', 'cancelall', 'vcpromote', 'vcdemote', 'refresh', 'rtitle', 'seek', 'mute', 'unmute',
f'stream@{Config.BOT_USERNAME}', f'logs@{Config.BOT_USERNAME}', f"replay@{Config.BOT_USERNAME}", f"yplay@{Config.BOT_USERNAME}", f"leave@{Config.BOT_USERNAME}", f"pause@{Config.BOT_USERNAME}", f"resume@{Config.BOT_USERNAME}", f"skip@{Config.BOT_USERNAME}", 
f"restart@{Config.BOT_USERNAME}", f"volume@{Config.BOT_USERNAME}", f"shuffle@{Config.BOT_USERNAME}", f"clearplaylist@{Config.BOT_USERNAME}", f"export@{Config.BOT_USERNAME}", f"import@{Config.BOT_USERNAME}", f"update@{Config.BOT_USERNAME}",
f'play@{Config.BOT_USERNAME}', f'schedule@{Config.BOT_USERNAME}', f'record@{Config.BOT_USERNAME}', f'slist@{Config.BOT_USERNAME}', f'cancel@{Config.BOT_USERNAME}', f'cancelall@{Config.BOT_USERNAME}', f'vcpromote@{Config.BOT_USERNAME}', 
f'vcdemote@{Config.BOT_USERNAME}', f'refresh@{Config.BOT_USERNAME}', f'rtitle@{Config.BOT_USERNAME}', f'seek@{Config.BOT_USERNAME}', f'mute@{Config.BOT_USERNAME}', f'unmute@{Config.BOT_USERNAME}'
]

allcmd = ["play", "player", f"play@{Config.BOT_USERNAME}", f"player@{Config.BOT_USERNAME}"] + admincmds

@Client.on_message(filters.command(admincmds) & ~admin_filter & chat_filter)
async def notforu(_, m: Message):
    k = await _.send_cached_media(chat_id=m.chat.id, file_id="CAADBQADEgQAAtMJyFVJOe6-VqYVzAI", caption="apko aagya ni hai", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⚡️Join Here', url='https://t.me/subin_works')]]))
    await delete_messages([m, k])

@Client.on_message(filters.command(allcmd) & ~chat_filter & filters.group)
async def not_chat(_, m: Message):
    if m.from_user is not None and m.from_user.id in Config.SUDO:
        buttons = [
            [
                InlineKeyboardButton('⚡️Change CHAT', callback_data='set_new_chat'),
            ],
            [
                InlineKeyboardButton('No', callback_data='closesudo'),
            ]
            ]
        await m.reply("keval exchangers adda group k lie bna hu ma contact @jagtarsidhu", reply_markup=InlineKeyboardMarkup(buttons))
        await delete_messages([m])
    else:
        buttons = [
            [
                InlineKeyboardButton('🧩 Contact here', url='https://t.me/jagtarsidhu'),
            ]
            ]
        await m.reply("<b>keval exchangers adda group k lie bna hu ma contact @jagtarsidhu</b>", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(buttons))

