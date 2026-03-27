import os
import re, sys
import json
import base64
import logging
import random
import asyncio
import string
import pytz
import time
from info import *
from .pmfilter import auto_filter 
from Script import script
from datetime import datetime
from database.refer import referdb
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardMarkup, WebAppInfo
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, ChatAdminRequired, UserNotParticipant
from database.ia_filterdb import Media, Media2, get_file_details, unpack_new_file_id, get_bad_files, save_file
from database.users_chats_db import db
from utils import stream_buttons, get_settings, save_group_settings, is_subscribed, is_req_subscribed, get_size, get_shortlink, is_check_admin, temp, get_readable_time, get_time, generate_settings_text, log_error, clean_filename, get_status

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

BATCH_FILES = {}

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS), big=True)
        except Exception:
            await message.react(emoji="⚡️")
            pass
    m = message
    if len(m.command) == 2 and m.command[1].startswith(('notcopy', 'sendall')):
        _, userid, verify_id, file_id = m.command[1].split("_", 3)
        user_id = int(userid)
        grp_id = temp.VERIFICATIONS.get(user_id, 0)
        settings = await get_settings(grp_id)         
        verify_id_info = await db.get_verify_id_info(user_id, verify_id)
        if not verify_id_info or verify_id_info["verified"]:
            return await message.reply("<b>ʟɪɴᴋ ᴇxᴘɪʀᴇᴅ ᴛʀʏ ᴀɢᴀɪɴ...</b>")
        ist_timezone = pytz.timezone('Asia/Kolkata')
        if await db.user_verified(user_id):
            key = "third_time_verified"
        else:
            key = "second_time_verified" if await db.is_user_verified(user_id) else "last_verified"
        current_time = datetime.now(tz=ist_timezone)
        result = await db.update_notcopy_user(user_id, {key:current_time})
        await db.update_verify_id_info(user_id, verify_id, {"verified":True})
        if key == "third_time_verified": 
            num = 3 
        else: 
            num =  2 if key == "second_time_verified" else 1 
        if key == "third_time_verified": 
            msg = script.THIRD_VERIFY_COMPLETE_TEXT
        else:
            msg = script.SECOND_VERIFY_COMPLETE_TEXT if key == "second_time_verified" else script.VERIFY_COMPLETE_TEXT
        if message.command[1].startswith('sendall'):
            verifiedfiles = f"https://telegram.me/{temp.U_NAME}?start=allfiles_{grp_id}_{file_id}"
        else:
            verifiedfiles = f"https://telegram.me/{temp.U_NAME}?start=file_{grp_id}_{file_id}"
        await client.send_message(settings['log'], script.VERIFIED_LOG_TEXT.format(m.from_user.mention, user_id, datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d %B %Y'), num))
        btn = [[InlineKeyboardButton("✅ ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ɢᴇᴛ ꜰɪʟᴇ ✅", url=verifiedfiles)]]
        reply_markup=InlineKeyboardMarkup(btn)
        dlt=await m.reply_photo(
            photo=(VERIFY_IMG),
            caption=msg.format(message.from_user.mention, get_readable_time(TWO_VERIFY_GAP)),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await asyncio.sleep(300)
        await dlt.delete()
        return
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        if not await db.get_chat(message.chat.id):
            await db.add_chat(message.chat.id, message.chat.title)
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))
        status = get_status()
        tb = await message.reply_text(f"<b>🔥 ʏᴇs {status},\nʜᴏᴡ ᴄᴀɴ ɪ ʜᴇʟᴘ ʏᴏᴜ??</b>")
        await asyncio.sleep(600)
        await tb.delete()
        await m.delete()
        return 
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        try:
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
        except Exception:
            pass
    if len(message.command) != 2:
        buttons = [[
                    InlineKeyboardButton('⇒ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ⇐', url=f'https://t.me/{temp.U_NAME}?startgroup=start')
                ],[
                    InlineKeyboardButton('🛠 ꜱᴇʀᴠɪᴄᴇꜱ', callback_data='donate'),
                    InlineKeyboardButton('ᴜᴘɢʀᴀᴅᴇ 🎫', callback_data='premium_info')
                ],[
                    InlineKeyboardButton('ᴀʙᴏᴜᴛ 📜', callback_data='about'),
                    InlineKeyboardButton('ʜᴇʟᴘ 💡', callback_data='help')
                ],[
                    InlineKeyboardButton('ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ☎️', url='https://telegram.me/master_xkid')
                ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m=await message.reply_sticker("CAACAgUAAxkBAAI47WjK1V24t_kyUL-ywJQQdxtaWnaeAAIMFgACpzEZVdpZS0jMvfn5HgQ")
        await asyncio.sleep(2)
        await m.delete()        
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, get_status(), temp.U_NAME or '', temp.B_NAME or ''),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    if message.command[1].startswith("reff_"):
        try:
            user_id = int(message.command[1].split("_")[1])
        except ValueError:
            await message.reply_text("Invalid refer!")
            return
        if user_id == message.from_user.id:
            await message.reply_text("ʜᴇʏ ᴅᴜᴅᴇ, ʏᴏᴜ ᴄᴀɴ'ᴛ ʀᴇꜰᴇʀ ʏᴏᴜʀsᴇʟꜰ 🤣!\n\nsʜᴀʀᴇ ʟɪɴᴋ ʏᴏᴜʀ ꜰʀɪᴇɴᴅ ᴀɴᴅ ɢᴇᴛ 𝟙𝟘 ʀᴇꜰᴇʀʀᴀʟ ᴘᴏɪɴᴛ. ɪꜰ ʏᴏᴜ ᴄᴏʟʟᴇᴄᴛ 𝟙𝟘𝟘 ʀᴇꜰᴇʀʀᴀʟ ᴘᴏɪɴᴛs, ᴛʜᴇɴ ʏᴏᴜ ᴄᴀɴ ɢᴇᴛ 𝟙 ᴍᴏɴᴛʜ ꜰʀᴇᴇ ᴘʀᴇᴍɪᴜᴍ ᴍᴇᴍʙᴇʀsʜɪᴘ.")
            return
        if referdb.is_user_in_list(message.from_user.id):
            await message.reply_text("ʏᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ᴀʟʀᴇᴀᴅʏ ɪɴᴠɪᴛᴇᴅ ❗")
            return
        if await db.is_user_exist(message.from_user.id): 
            await message.reply_text("‼️ ʏᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ᴀʟʀᴇᴀᴅʏ ɪɴᴠɪᴛᴇᴅ ᴏʀ ᴊᴏɪɴᴇᴅ.")
            return 
        try:
            uss = await client.get_users(user_id)
        except Exception:
            return 	    
        referdb.add_user(message.from_user.id)
        fromuse = referdb.get_refer_points(user_id) + 10
        if fromuse == 100:
            referdb.add_refer_points(user_id, 0) 
            await message.reply_text(f"🎉 𝗖𝗼𝗻𝗴𝗿𝗮𝘁𝘂𝗹𝗮𝘁𝗶𝗼𝗻𝘀! 𝗬𝗼𝘂 𝘄𝗼𝗻 𝟭𝟬 𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹 𝗽𝗼𝗶𝗻𝘁 𝗯𝗲𝗰𝗮𝘂𝘀𝗲 𝗬𝗼𝘂 𝗵𝗮𝘃𝗲 𝗯𝗲𝗲𝗻 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗜𝗻𝘃𝗶𝘁𝗲𝗱 ☞ {uss.mention}!")		    
            await message.reply_text(user_id, f"You have been successfully invited by {message.from_user.mention}!") 	
            seconds = 2592000
            if seconds > 0:
                expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
                user_data = {"id": user_id, "expiry_time": expiry_time}  # Using "id" instead of "user_id"  
                await db.update_user(user_data)  # Use the update_user method to update or insert user data		    
                await client.send_message(
                chat_id=user_id,
                text=f"<b>ʜʏ {uss.mention}\n\nʏᴏᴜ ɢᴏᴛ 𝟷 ᴍᴏɴᴛʜ ᴘʀᴇᴍɪᴜᴍ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ʙʏ ɪɴᴠɪᴛɪɴɢ 𝟷𝟶 ᴜsᴇʀs ❗", disable_web_page_preview=True              
                )
            for admin in ADMINS:
                await client.send_message(chat_id=admin, text=f"sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ʙʏ:\n\nᴜsᴇʀ: {uss.mention}\n\nɪᴅ: {uss.id}!")	
        else:
            referdb.add_refer_points(user_id, fromuse)
            await message.reply_text(f"You have been successfully invited by {uss.mention}!")
            await client.send_message(user_id, f"𝗖𝗼𝗻𝗴𝗿𝗮𝘁𝘂𝗹𝗮𝘁𝗶𝗼𝗻𝘀! 𝗬𝗼𝘂 𝘄𝗼𝗻 𝟭𝟬 𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹 𝗽𝗼𝗶𝗻𝘁 𝗯𝗲𝗰𝗮𝘂𝘀𝗲 𝗬𝗼𝘂 𝗵𝗮𝘃𝗲 𝗯𝗲𝗲𝗻 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆 𝗜𝗻𝘃𝗶𝘁𝗲𝗱 ☞{message.from_user.mention}!")
        return

    if len(message.command) == 2 and message.command[1].startswith('getfile'):
        movies = message.command[1].split("-", 1)[1] 
        movie = movies.replace('-',' ')
        message.text = movie 
        await auto_filter(client, message) 
        return
    data = message.command[1]
    try:
        _, grp_id, file_id = data.split("_", 2)
        grp_id = int(grp_id)
    except:
        grp_id = 0
        file_id = data
    file_details_task = asyncio.create_task(get_file_details(file_id))
    if not await db.has_premium_access(message.from_user.id): 
        try:
            btn = []
            chat = grp_id
            settings      = await get_settings(chat)
            fsub_channels = list(dict.fromkeys((settings.get('fsub', []) if settings else [])+ AUTH_CHANNELS))
            if fsub_channels:
                btn += await is_subscribed(client, message.from_user.id, fsub_channels)
            if AUTH_REQ_CHANNELS:
                btn += await is_req_subscribed(client, message.from_user.id, AUTH_REQ_CHANNELS)
            if btn:
                if len(message.command) > 1 and "_" in message.command[1]:
                    kk, file_id = message.command[1].split("_", 1)
                    btn.append([InlineKeyboardButton("♻️ ᴛʀʏ ᴀɢᴀɪɴ ♻️", callback_data=f"checksub#{kk}#{file_id}")])
                    reply_markup = InlineKeyboardMarkup(btn)
                await message.reply_photo(
                    photo=random.choice(PICS),
                    caption=(f"""{message.from_user.mention}\n\n நீங்கள் கேட்கும் மூவி  தேவை என்றால், கீழே உள்ள 📥 Movies Channel - லில் சேர வேண்டும் 👇✅

அந்த மூவீஸ் சேனலில் இணைந்த பிறகு 🔄 "Try Again Button" கிளிக் செய்யவும் ✅

அப்போது உங்கள் மூவி வரும் இங்கே ✅👇

❗️ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴍʏ ᴍᴏᴠɪᴇꜱ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ʙᴏᴛ 👇

📥 ᴀꜰᴛᴇʀ ᴊᴏɪɴᴇᴅ ᴍᴏᴠɪᴇꜱ ᴄʜᴀɴɴᴇʟ👇 ᴄʟɪᴄᴋ ᴛʀʏ ᴀɢᴀɪɴ ʙᴜᴛᴛᴏɴ ʏᴏᴜʀ ᴀꜱᴋᴇᴅ ꜰɪʟᴇ ᴡɪʟʟ ᴄᴏᴍᴇ ✅."""),
                    reply_markup=reply_markup,
                    parse_mode=enums.ParseMode.HTML
                )
                return
        except Exception as e:
            await log_error(client, f"❗️ Force Sub Error:\n\n{repr(e)}")
            logger.error(f"❗️ Force Sub Error:\n\n{repr(e)}")

    user_id = m.from_user.id
    if not await db.has_premium_access(user_id):
        try:
            grp_id = int(grp_id)
            user_verified = await db.is_user_verified(user_id)
            settings = await get_settings(grp_id)
            is_second_shortener = await db.use_second_shortener(user_id, settings.get('verify_time', TWO_VERIFY_GAP)) 
            is_third_shortener = await db.use_third_shortener(user_id, settings.get('third_verify_time', THREE_VERIFY_GAP))
            if settings.get("is_verify", IS_VERIFY) and (not user_verified or is_second_shortener or is_third_shortener):
                verify_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
                await db.create_verify_id(user_id, verify_id)
                temp.VERIFICATIONS[user_id] = grp_id
                if message.command[1].startswith('allfiles'):
                    verify = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=sendall_{user_id}_{verify_id}_{file_id}", grp_id, is_second_shortener, is_third_shortener)
                else:
                    verify = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=notcopy_{user_id}_{verify_id}_{file_id}", grp_id, is_second_shortener, is_third_shortener)
                if is_third_shortener:
                    howtodownload = settings.get('tutorial_3', TUTORIAL_3)
                else:
                    howtodownload = settings.get('tutorial_2', TUTORIAL_2) if is_second_shortener else settings.get('tutorial', TUTORIAL)
                buttons = [[
                    InlineKeyboardButton(text="♻️ ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ᴠᴇʀɪꜰʏ ♻️", url=verify)
                ],[
                    InlineKeyboardButton(text="⁉️ ʜᴏᴡ ᴛᴏ ᴠᴇʀɪꜰʏ ⁉️", url=howtodownload)
                ],[
                    InlineKeyboardButton(text="😁 ʙᴜʏ sᴜʙsᴄʀɪᴘᴛɪᴏɴ - ɴᴏ ɴᴇᴇᴅ ᴛᴏ ᴠᴇʀɪғʏ 😁", callback_data='buy_info')
            
                ]]
                reply_markup=InlineKeyboardMarkup(buttons)
                if await db.user_verified(user_id): 
                    msg = script.THIRD_VERIFICATION_TEXT
                else:            
                    msg = script.SECOND_VERIFICATION_TEXT if is_second_shortener else script.VERIFICATION_TEXT
                n=await m.reply_text(
                    text=msg.format(message.from_user.mention),
                    protect_content = True,
                    reply_markup=reply_markup,
                    parse_mode=enums.ParseMode.HTML
                )
                await asyncio.sleep(300) 
                await n.delete()
                await m.delete()
                return
        except Exception as e:
            print(f"Error In Verification - {e}")
            pass

    files_ = await file_details_task
    if data.startswith("allfiles"):
        try:
            files = temp.GETALL.get(file_id)
            if not files:
                return await message.reply('<b><i>ɴᴏ ꜱᴜᴄʜ ꜰɪʟᴇ ᴇxɪꜱᴛꜱ !</b></i>')
            filesarr = []
            cover = None
            for file in files:
                file_id = file.file_id
                files_ = await get_file_details(file_id)
                files1 = files_[0]
                title = clean_filename(files1.file_name)
                cover = files1.cover
                size = get_size(files1.file_size)
                f_caption = files1.caption
                settings = await get_settings(int(grp_id))
                CAPTION = settings.get('caption', FILE_CAPTION)
                if CAPTION:
                    try:
                        f_caption=CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                    except Exception as e:
                        logger.exception(e)
                        f_caption = f_caption
                if f_caption is None:
                    f_caption = f"{clean_filename(files1.file_name)}"
                btn = await stream_buttons(message.from_user.id, file_id)
                msg = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    cover=cover,
                    file_id=file_id,
                    caption=f_caption,
                    protect_content=settings.get('file_secure', PROTECT_CONTENT),
                    reply_markup=InlineKeyboardMarkup(btn)
                )
                filesarr.append(msg)
            k = await client.send_message(chat_id=message.from_user.id, text=f"<i>⚠️ ᴛʜɪꜱ ꜰɪʟᴇ/ᴠɪᴅᴇᴏ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ {get_time(DELETE_TIME)} 🫥 (ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ).</i>\n\n<blockquote><b>ᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ꜰɪʟᴇ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇʀᴇ.</b></blockquote>")
            await asyncio.sleep(DELETE_TIME)
            for x in filesarr:
                await x.delete()
            await k.edit_text("<b>ʏᴏᴜʀ ᴀʟʟ ᴠɪᴅᴇᴏꜱ/ꜰɪʟᴇꜱ ᴀʀᴇ ᴅᴇʟᴇᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ !\nᴋɪɴᴅʟʏ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ</b>")
            return
        except Exception as e:
            logger.exception(e)
            return

    user = message.from_user.id
    is_premium = await db.has_premium_access(user)
    settings = await get_settings(int(grp_id))
    if not files_:
        raw = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
        sep = raw.find(b"_")
        if sep == -1:
            raise ValueError("Invalid encoded data")
        pre = raw[:sep].decode("ascii")
        file_id = raw[sep + 1:].decode("latin1")
        # pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("utf-8")).split("_", 1)
        try:
            cover = None
            if COVER:
                details= await get_file_details(file_id)
                cover = details.get('cover', None)
            btn = await stream_buttons(user, file_id)
            if IS_FILE_LIMIT and not is_premium:
                used = await db.get_user_file_count(user)
                hours, minutes = await db.get_time_until_reset(user)
                if used >= FILES_LIMIT:
                    return await message.reply_photo(
                        photo=random.choice(PICS),
                        caption = f"<b>{message.from_user.mention},\n\n🚫 ʏᴏᴜ’ᴠᴇ ʀᴇᴀᴄʜᴇᴅ ʏᴏᴜʀ ᴅᴀɪʟʏ ʟɪᴍɪᴛ ᴏꜰ {FILES_LIMIT} ꜰɪʟᴇꜱ.\n\n⏱️ ʏᴏᴜʀ ʟɪᴍɪᴛ ʀᴇꜱᴇᴛꜱ ɪɴ {hours}h {minutes}m\n\n💎 <i>ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ꜰᴏʀ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ᴀɴᴅ ᴇxᴄʟᴜsɪᴠᴇ ꜰᴇᴀᴛᴜʀᴇs.</i></b>",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ 💎", callback_data='premium')]]),
                        parse_mode=enums.ParseMode.HTML
                    )

            msg = await client.send_cached_media(
                chat_id=user,
                cover=cover,
                file_id=file_id,
                protect_content=settings.get('file_secure', PROTECT_CONTENT),
                reply_markup=InlineKeyboardMarkup(btn))

            filetype = msg.media
            file = getattr(msg, filetype.value)
            title = clean_filename(file.file_name)
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            settings = await get_settings(int(grp_id))
            CAPTION = settings.get('caption', FILE_CAPTION)
            if CAPTION:
                try:
                    f_caption=CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    return
            if IS_FILE_LIMIT and not is_premium:
                await db.increment_file_count(user)
                used = await db.get_user_file_count(user)
                limit_info = f"\n\n📊 ʏᴏᴜ ʜᴀᴠᴇ ʀᴇᴄᴇɪᴠᴇᴅ {used}/{FILES_LIMIT} ꜰʀᴇᴇ ꜰɪʟᴇꜱ ᴛᴏᴅᴀʏ."
                f_caption += limit_info
            await msg.edit_caption(f_caption, reply_markup=InlineKeyboardMarkup(btn))
            k = await msg.reply(f"<i>⚠️ ᴛʜɪꜱ ꜰɪʟᴇ/ᴠɪᴅᴇᴏ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ {get_time(DELETE_TIME)} 🫥 (ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ).</i>\n\n<blockquote><b>ᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ꜰɪʟᴇ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇʀᴇ.</b></blockquote>", quote=True)     
            await asyncio.sleep(DELETE_TIME)
            await msg.delete()
            await k.edit_text("<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ/ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!</b>")
            return
        except Exception as e:
            logger.exception(e)
            pass
        return await message.reply('ɴᴏ ꜱᴜᴄʜ ꜰɪʟᴇ ᴇxɪꜱᴛꜱ !')
    
    files = files_[0]
    if IS_FILE_LIMIT and not is_premium:
        used = await db.get_user_file_count(user)
        hours, minutes = await db.get_time_until_reset(user)
        if used >= FILES_LIMIT:
            return await message.reply_photo(
                photo=random.choice(PICS),
                caption = f"<b>{message.from_user.mention},\n\n🚫 ʏᴏᴜ’ᴠᴇ ʀᴇᴀᴄʜᴇᴅ ʏᴏᴜʀ ᴅᴀɪʟʏ ʟɪᴍɪᴛ ᴏꜰ {FILES_LIMIT} ꜰɪʟᴇꜱ.\n\n⏱️ ʏᴏᴜʀ ʟɪᴍɪᴛ ʀᴇꜱᴇᴛꜱ ɪɴ {hours}h {minutes}m\n\n<blockquote>💎 <i>ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ꜰᴏʀ ᴜɴʟɪᴍɪᴛᴇᴅ ᴀᴄᴄᴇꜱꜱ ᴀɴᴅ ᴇxᴄʟᴜsɪᴠᴇ ꜰᴇᴀᴛᴜʀᴇs.</i></blockquote></b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ 💎", callback_data='premium')]]),
                parse_mode=enums.ParseMode.HTML
            )

    file_quality = getattr(files, "quality", "")
    if QUALITY_LIMIT and not is_premium:
        if not any(q in (files.file_name or "").lower() for q in FREE_QUALITIES):
            tb = ", ".join(FREE_QUALITIES).upper()
            await message.reply_photo(
                photo=random.choice(PICS),
                caption = f"<b>{message.from_user.mention},\n\nᴛʜɪs ꜰɪʟᴇ ɪs ᴀᴠᴀɪʟᴀʙʟᴇ ᴏɴʟʏ ꜰᴏʀ ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs.\n\n👥 ꜰʀᴇᴇ ᴜsᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss {tb} ǫᴜᴀʟɪᴛɪᴇꜱ ᴏɴʟʏ.\n\n<blockquote>💎 <i>ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴜɴʟᴏᴄᴋ ʜɪɢʜᴇʀ ǫᴜᴀʟɪᴛʏ ᴄᴏɴᴛᴇɴᴛ ᴀɴᴅ ᴇxᴄʟᴜsɪᴠᴇ ꜰᴇᴀᴛᴜʀᴇs.</i></blockquote></b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💎 ᴜɴʟᴏᴄᴋ ᴘʀᴇᴍɪᴜᴍ 💎", callback_data='premium')]]),
                parse_mode=enums.ParseMode.HTML
            )
            return

    title = clean_filename(files.file_name)
    size = get_size(files.file_size)
    cover = files.cover if files.cover else None
    f_caption = files.caption
    settings = await get_settings(int(grp_id))            
    CAPTION = settings.get('caption', FILE_CAPTION)
    if CAPTION:
        try:
            f_caption=CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception as e:
            logger.exception(e)
            f_caption = f_caption

    if f_caption is None:
        f_caption = clean_filename(files.file_name)
    if IS_FILE_LIMIT and not is_premium:
        await db.increment_file_count(user)
        used = await db.get_user_file_count(user)
        limit_info = f"\n\n📊 ʏᴏᴜ ʜᴀᴠᴇ ʀᴇᴄᴇɪᴠᴇᴅ {used}/{FILES_LIMIT} ꜰʀᴇᴇ ꜰɪʟᴇꜱ ᴛᴏᴅᴀʏ."
        f_caption += limit_info
    btn = await stream_buttons(user, file_id)
    msg = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        cover=cover,
        caption=f_caption,
        protect_content=settings.get('file_secure', PROTECT_CONTENT),
        reply_markup=InlineKeyboardMarkup(btn)
    )
    k = await msg.reply(f"<i>⚠️ ᴛʜɪꜱ ꜰɪʟᴇ/ᴠɪᴅᴇᴏ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ {get_time(DELETE_TIME)} 🫥 (ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ).</i>\n\n<blockquote><b>ᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ꜰɪʟᴇ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇʀᴇ.</b></blockquote>", quote=True)     
    await asyncio.sleep(DELETE_TIME)
    await msg.delete()
    await k.edit_text("<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ/ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!</b>")
    return

@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    try:
        await message.reply_document('TechifyBots.txt', caption="📑 **ʟᴏɢꜱ**")
    except Exception as e:
        await message.reply(str(e))

@Client.on_message(filters.command('save') & filters.user(ADMINS))
async def save_file_handler(bot, message):
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("ᴘʀᴏᴄᴇssɪɴɢ...", quote=True)
    else:
        await message.reply('ʀᴇᴘʟʏ ᴛᴏ ꜰɪʟᴇ ᴡɪᴛʜ /save ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ sᴀᴠᴇ', quote=True)
        return
    try:
        for file_type in ("document", "video", "audio"):
            media = getattr(reply, file_type, None)
            if media is not None:
                break
        else:
            await msg.edit('Tʜɪs ɪs ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ ꜰɪʟᴇ ꜰᴏʀᴍᴀᴛ')
            return
        file_id, file_ref = unpack_new_file_id(media.file_id)
        media.file_type = file_type
        media.caption = reply.caption
        success, status = await save_file(media)
        if success:
            await msg.edit('ꜰɪʟᴇ ɪs sᴜᴄᴄᴇssꜰᴜʟʟʏ sᴀᴠᴇᴅ ᴛᴏ ᴅᴀᴛᴀʙᴀsᴇ ✅')
        elif status == 0:
            await msg.edit('ꜰɪʟᴇ ᴀʟʀᴇᴀᴅʏ ᴇxɪsᴛs ɪɴ ᴅᴀᴛᴀʙᴀsᴇ ⚠️')
        elif status == 2:
            await msg.edit('ᴇʀʀᴏʀ: ꜰɪʟᴇ ᴠᴀʟɪᴅᴀᴛɪᴏɴ ꜰᴀɪʟᴇᴅ ❌')
        else:
            await msg.edit('ᴇʀʀᴏʀ: ꜰᴀɪʟᴇᴅ ᴛᴏ sᴀᴠᴇ ꜰɪʟᴇ ❌')
    except Exception as e:
        logger.exception(e)
        await msg.edit(f'ᴀɴ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: {e} ❌')

@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("ᴘʀᴏᴄᴇssɪɴɢ...", quote=True)
    else:
        await message.reply('ʀᴇᴘʟʏ ᴛᴏ ꜰɪʟᴇ ᴡɪᴛʜ /delete ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('ᴛʜɪs ɪs ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ ꜰɪʟᴇ ꜰᴏʀᴍᴀᴛ')
        return
    
    file_id, file_ref = unpack_new_file_id(media.file_id)
    if await Media.count_documents({'file_id': file_id}):
        result = await Media.collection.delete_one({
            '_id': file_id,
        })
    else:
        result = await Media2.collection.delete_one({
            '_id': file_id,
        })
    if result.deleted_count:
        await msg.edit('ꜰɪʟᴇ ɪs sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ ✅')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count:
            await msg.edit('ꜰɪʟᴇ ɪs sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ ✅')
        else:
            result = await Media2.collection.delete_many({
                'file_name': file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count:
                await msg.edit('ꜰɪʟᴇ ɪs sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ')
            else:
                result = await Media.collection.delete_many({
                    'file_name': media.file_name,
                    'file_size': media.file_size,
                    'mime_type': media.mime_type
                })
                if result.deleted_count:
                    await msg.edit('ꜰɪʟᴇ ɪs sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ ✅')
                else:
                    result = await Media2.collection.delete_many({
                        'file_name': media.file_name,
                        'file_size': media.file_size,
                        'mime_type': media.mime_type
                    })
                    if result.deleted_count:
                        await msg.edit('ꜰɪʟᴇ ɪs sᴜᴄᴄᴇssꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴅᴀᴛᴀʙᴀsᴇ ✅')
                    else:
                        await msg.edit('ꜰɪʟᴇ ɴᴏᴛ ꜰᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀsᴇ ❌')

@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text('ᴛʜɪꜱ ᴡɪʟʟ ᴅᴇʟᴇᴛᴇ ᴀʟʟ ʏᴏᴜʀ ɪɴᴅᴇxᴇᴅ ꜰɪʟᴇꜱ !\nᴅᴏ ʏᴏᴜ ꜱᴛɪʟʟ ᴡᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ?', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="⚠️ ʏᴇꜱ ⚠️", callback_data="autofilter_delete")], [InlineKeyboardButton(text="❌ ɴᴏ ❌", callback_data="close_data")]]), quote=True)

@Client.on_message(filters.command('settings'))
async def settings(client, message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return await message.reply(f"ʏᴏᴜ'ʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ.")
    chat_type = message.chat.type
    if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        if not await is_check_admin(client, grp_id, message.from_user.id):
            return await message.reply_text(script.ADMIN_ALRT_TXT)
        await db.connect_group(grp_id, user_id)
        btn = [[
                InlineKeyboardButton("👤 ᴏᴘᴇɴ ɪɴ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ 👤", callback_data=f"opnsetpm#{grp_id}")
              ],[
                InlineKeyboardButton("👥 ᴏᴘᴇɴ ʜᴇʀᴇ 👥", callback_data=f"opnsetgrp#{grp_id}")
              ]]
        await message.reply_text(
                text="<b>ᴡʜᴇʀᴇ ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴏᴘᴇɴ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ? ⚙️</b>",
                reply_markup=InlineKeyboardMarkup(btn),
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=message.id
        )
    elif chat_type == enums.ChatType.PRIVATE:
        connected_groups = await db.get_connected_grps(user_id)
        if not connected_groups:
            return await message.reply_text("ɴᴏ ᴄᴏɴɴᴇᴄᴛᴇᴅ ɢʀᴏᴜᴘ ꜰᴏᴜɴᴅ.")
        group_list = []
        for group in connected_groups:
            try:
                Chat = await client.get_chat(group)
                group_list.append([ InlineKeyboardButton(text=Chat.title, callback_data=f"grp_pm#{Chat.id}") ])
            except Exception as e:
                print(f"Error In PM Settings Button - {e}")
                pass
        await message.reply_text("⚠️ ꜱᴇʟᴇᴄᴛ ᴛʜᴇ ɢʀᴏᴜᴘ ᴡʜᴏꜱᴇ ꜱᴇᴛᴛɪɴɢꜱ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄʜᴀɴɢᴇ.\n\nɪꜰ ʏᴏᴜʀ ɢʀᴏᴜᴘ ɪꜱ ɴᴏᴛ ꜱʜᴏᴡɪɴɢ ʜᴇʀᴇ,\nᴜꜱᴇ /reload ɪɴ ᴛʜᴀᴛ ɢʀᴏᴜᴘ ᴀɴᴅ ɪᴛ ᴡɪʟʟ ᴀᴘᴘᴇᴀʀ ʜᴇʀᴇ.", reply_markup=InlineKeyboardMarkup(group_list))

@Client.on_message(filters.command('reload'))
async def connect_group(client, message):
    user_id = message.from_user.id
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        await db.connect_group(message.chat.id, user_id)
        await message.reply_text(f"ɢʀᴏᴜᴘ ʀᴇʟᴏᴀᴅᴇᴅ ✅\nɴᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴍᴀɴᴀɢᴇ ᴛʜɪs ɢʀᴏᴜᴘ ꜰʀᴏᴍ ᴘᴍ.")
    elif message.chat.type == enums.ChatType.PRIVATE:
        if len(message.command) < 2:
            await message.reply_text("Example: /reload 123456789")
            return
        try:
            group_id = int(message.command[1])
            if not await is_check_admin(client, group_id, user_id):
                await message.reply_text(script.ADMIN_ALRT_TXT)
                return
            chat = await client.get_chat(group_id)
            await db.connect_group(group_id, user_id)
            await message.reply_text(f"ʟɪɴᴋᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ ✅ {chat.title} ᴛᴏ ᴘᴍ.")
        except:
            await message.reply_text("Invalid group ID or error occurred.")

@Client.on_message(filters.command('template'))
async def save_template(client, message):
    sts = await message.reply("ᴄʜᴇᴄᴋɪɴɢ ᴛᴇᴍᴘʟᴀᴛᴇ...")
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return await message.reply("ʏᴏᴜ'ʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ.")
    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await sts.edit("⚠️ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ᴀ ɢʀᴏᴜᴘ ᴄʜᴀᴛ.")
    group_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, group_id, user_id):
        await message.reply_text(script.ADMIN_ALRT_TXT)
        return
    if len(message.command) < 2:
        return await sts.edit("⚠️ ɴᴏ ᴛᴇᴍᴘʟᴀᴛᴇ ᴘʀᴏᴠɪᴅᴇᴅ!")
    template = message.text.split(" ", 1)[1]
    await save_group_settings(group_id, 'template', template)
    await sts.edit(f"✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ᴛᴇᴍᴘʟᴀᴛᴇ ꜰᴏʀ <code>{title}</code> ᴛᴏ:\n\n{template}")

@Client.on_message(filters.command("request"))
async def requests(bot, message):
    if REQST_CHANNEL is None:
        return
    user = message.from_user
    reporter = str(user.id)
    mention = user.mention

    if len(message.command) > 1:
        content = " ".join(message.command[1:])
    else:
        await message.reply_text(f"<b>📝 ʀᴇǫᴜᴇsᴛ ꜰᴏʀᴍᴀᴛ:\n\n/request ꜰɪʟᴇs ɴᴀᴍᴇ | ʏᴇᴀʀ</b>", quote=True)
        return
    try:
        reported_post = await bot.send_message(
            chat_id=REQST_CHANNEL,
            text=f"<b>📝 ʀᴇǫᴜᴇꜱᴛ : {content}\n\n🕵️ ʙʏ : {mention}\n📖 ɪᴅ : {reporter}</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('ꜱʜᴏᴡ ᴏᴘᴛɪᴏɴꜱ', callback_data=f'show_option#{reporter}')]])
        )
        link = await bot.create_chat_invite_link(int(REQST_CHANNEL))
        reply_btn = [[
            InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
            InlineKeyboardButton('ᴠɪᴇᴡ ʀᴇǫᴜᴇꜱᴛ', url=f"{reported_post.link}")
        ]]
        await message.reply_text(f"<b><i>ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ᴀᴅᴅᴇᴅ, ᴄʜᴇᴄᴋ ɪᴛꜱ ꜱᴛᴀᴛᴜꜱ ʙᴇʟᴏᴡ.</i></b>", reply_markup=InlineKeyboardMarkup(reply_btn), quote=True)
    except Exception as e:
        await message.reply_text(f"⚠️ error: {e}")

@Client.on_message(filters.command("send") & filters.user(ADMINS))
async def send_msg(bot, message):
    if message.reply_to_message:
        target_id = message.text.split(" ", 1)[1]
        out = "Users Saved In DB Are:\n\n"
        success = False
        try:
            user = await bot.get_users(target_id)
            users = await db.get_all_users()
            async for usr in users:
                out += f"{usr['id']}"
                out += '\n'
            if str(user.id) in str(out):
                await message.reply_to_message.copy(int(user.id))
                success = True
            else:
                success = False
            if success:
                await message.reply_text(f"<b>ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴇɴᴛ ᴛᴏ {user.mention}.</b>")
            else:
                await message.reply_text("<b>ᴛʜɪꜱ ᴜꜱᴇʀ ᴅɪᴅɴ'ᴛ ꜱᴛᴀʀᴛᴇᴅ ᴛʜɪꜱ ʙᴏᴛ ʏᴇᴛ !</b>")
        except Exception as e:
            await message.reply_text(f"<b>Error: {e}</b>")
    else:
        await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴀꜱ ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴍᴇꜱꜱᴀɢᴇ ᴜꜱɪɴɢ ᴛʜᴇ ᴛᴀʀɢᴇᴛ ᴄʜᴀᴛ ɪᴅ. ꜰᴏʀ ᴇɢ:  /send ᴜꜱᴇʀɪᴅ</b>")

@Client.on_message(filters.command("deletefiles") & filters.user(ADMINS))
async def deletemultiplefiles(bot, message):
    chat_type = message.chat.type
    if chat_type != enums.ChatType.PRIVATE:
        return await message.reply_text(f"<b>Hey {message.from_user.mention}, This command won't work in groups. It only works on my PM !</b>")
    try:
        keyword = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text(f"<b>Hey {message.from_user.mention}, Give me a keyword along with the command to delete files.</b>")
    k = await bot.send_message(chat_id=message.chat.id, text=f"<b>Fetching Files for your query {keyword} on DB... Please wait...</b>")
    files, total = await get_bad_files(keyword)
    total = len(files)
    if total == 0:
        await k.edit_text(f"<b>No files found for your query {keyword} !</b>")
        await asyncio.sleep(DELETE_TIME)
        await k.delete()
        return
    await k.delete()
    btn = [[
       InlineKeyboardButton("⚠️ 𝖸𝖾𝗌, 𝖢𝗈𝗇𝗍𝗂𝗇𝗎𝖾 !", callback_data=f"killfilesdq#{keyword}")
       ],[
       InlineKeyboardButton("❌ 𝖭𝗈, 𝖠𝖻𝗈𝗋𝗍 𝗈𝗉𝖾𝗋𝖺𝗍𝗂𝗈𝗇 !", callback_data="close_data")
    ]]
    await message.reply_text(
        text=f"<b>Found {total} files for your query {keyword} !\n\nDo you want to delete?</b>",
        reply_markup=InlineKeyboardMarkup(btn),
        parse_mode=enums.ParseMode.HTML
    )

@Client.on_message(filters.private & filters.command("pm_search") & filters.user(ADMINS))
async def set_pm_search(client, message):
    bot_id = client.me.id
    try:
        option = message.text.split(" ", 1)[1].strip().lower()
        enable_status = option in ['on', 'true']
    except (IndexError, ValueError):
        await message.reply_text("<b>💔 Invalid option. Please send 'on' or 'off' after the command..</b>")
        return
    try:
        await db.update_pm_search_status(bot_id, enable_status)
        response_text = (
            "<b> ᴘᴍ ꜱᴇᴀʀᴄʜ ᴇɴᴀʙʟᴇᴅ ✅</b>" if enable_status
            else "<b> ᴘᴍ ꜱᴇᴀʀᴄʜ ᴅɪꜱᴀʙʟᴇᴅ ❌</b>"
        )
        await message.reply_text(response_text)
    except Exception as e:
        logger.error(f"Error in set_pm_search: {e}")
        await message.reply_text(f"<b>❗ An error occurred: {e}</b>")

@Client.on_message(filters.private & filters.command("notify") & filters.user(ADMINS))
async def update_notification(client, message):
    bot_id = client.me.id
    try:
        option = message.text.split(" ", 1)[1].strip().lower()
        enable_status = option in ['on', 'true']
    except (IndexError, ValueError):
        await message.reply_text("<b>💔 Invalid option. Please send 'on' or 'off' after the command.</b>")
        return
    try:
        await db.update_movie_update_status(bot_id, enable_status)
        response_text = (
            "<b>ᴜᴘᴅᴀᴛᴇ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ ᴇɴᴀʙʟᴇᴅ ✅</b>" if enable_status
            else "<b>ᴜᴘᴅᴀᴛᴇ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ ᴅɪꜱᴀʙʟᴇᴅ ❌</b>"
        )
        await message.reply_text(response_text)
    except Exception as e:
        logger.error(f"Error in update_notification: {e}")
        await message.reply_text(f"<b>❗ An error occurred: {e}</b>")

@Client.on_message(filters.command("restart") & filters.user(ADMINS))
async def stop_button(bot, message):
    msg = await bot.send_message(text="<b><i>ʙᴏᴛ ɪꜱ ʀᴇꜱᴛᴀʀᴛɪɴɢ</i></b>", chat_id=message.chat.id)
    await asyncio.sleep(3)
    await msg.edit("<b><i><u>ʙᴏᴛ ɪꜱ ʀᴇꜱᴛᴀʀᴛᴇᴅ</u> ✅</i></b>")
    os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_message(filters.command("del_msg") & filters.user(ADMINS))
async def del_msg(client, message):
    confirm_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("ʏᴇs", callback_data="confirm_del_yes"),
        InlineKeyboardButton("ɴᴏ", callback_data="confirm_del_no")
    ]])
    sent_message = await message.reply_text("⚠️ ᴀʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄʟᴇᴀʀ ᴛʜᴇ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ ʟɪsᴛ ?\n\n ᴅᴏ ʏᴏᴜ ꜱᴛɪʟʟ ᴡᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ?", reply_markup=confirm_markup)
    await asyncio.sleep(60)
    try:
        await sent_message.delete()
    except Exception as e:
        print(f"Error deleting the message: {e}")

@Client.on_callback_query(filters.regex('^confirm_del_'))
async def confirmation_handler(client, callback_query):
    action = callback_query.data.split("_")[-1]
    if action == "yes":
        await db.delete_all_msg()
        await callback_query.message.edit_text('🧹 ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ ʟɪsᴛ ʜᴀs ʙᴇᴇɴ ᴄʟᴇᴀʀᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ ✅')
    elif action == "no":
        await callback_query.message.delete()
    await callback_query.answer()

@Client.on_message(filters.command('caption'))
async def save_caption(client, message):
    grp_id = message.chat.id
    title = message.chat.title
    invite_link = await client.export_chat_invite_link(grp_id)
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text(script.ADMIN_ALRT_TXT)
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    try:
        caption = message.text.split(" ", 1)[1]
    except:
        return await message.reply_text("<code>ɢɪᴠᴇ ᴍᴇ ᴀ ᴄᴀᴘᴛɪᴏɴ ᴀʟᴏɴɢ ᴡɪᴛʜ ɪᴛ.\n\nᴇxᴀᴍᴘʟᴇ -\n\nꜰᴏʀ ꜰɪʟᴇ ɴᴀᴍᴇ - <code>{file_name}</code>\nꜰᴏʀ ꜰɪʟᴇ ꜱɪᴢᴇ - <code>{file_size}</code>\n\n<code>/caption {file_name}</code></code>")
    await save_group_settings(grp_id, 'caption', caption)
    await message.reply_text(f"ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄʜᴀɴɢᴇᴅ ᴄᴀᴘᴛɪᴏɴ ꜰᴏʀ {title}\n\nᴄᴀᴘᴛɪᴏɴ - {caption}", disable_web_page_preview=True)
    await client.send_message(LOG_API_CHANNEL, f"#Set_Caption\n\nɢʀᴏᴜᴘ ɴᴀᴍᴇ : {title}\n\nɢʀᴏᴜᴘ ɪᴅ: {grp_id}\nɪɴᴠɪᴛᴇ ʟɪɴᴋ : {invite_link}\n\nᴜᴘᴅᴀᴛᴇᴅ ʙʏ : {message.from_user.username}")

@Client.on_message(filters.command(["tutorial", "tutorial2", "tutorial3"]))
async def set_tutorial(client, message: Message):
    grp_id = message.chat.id
    title = message.chat.title
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text(f"<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...\n\nGroup Name: {title}\nGroup ID: {grp_id}</b>")
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text(script.ADMIN_ALRT_TXT)
    try:
        tutorial_link = message.text.split(" ", 1)[1]
    except IndexError:
        return await message.reply_text(
            f"<b>ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ !!\n\nᴜꜱᴇ ʟɪᴋᴇ ᴛʜɪꜱ -</b>\n\n"
            f"<code>/{message.command[0]} https://youtu.be/jcIrYkVy0d0</code>"
        )
    if message.command[0] == "tutorial":
        tutorial_key = "tutorial"
    elif message.command[0] == "tutorial2":
        tutorial_key = "tutorial_2"
    elif message.command[0] == "tutorial3":
        tutorial_key = "tutorial_3"

    await save_group_settings(grp_id, tutorial_key, tutorial_link)
    invite_link = await client.export_chat_invite_link(grp_id)
    await message.reply_text(
        f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄʜᴀɴɢᴇᴅ {tutorial_key.replace('_', ' ').title()} ꜰᴏʀ {title}</b>\n\n"
        f"ʟɪɴᴋ - {tutorial_link}",
        disable_web_page_preview=True
    )
    await client.send_message(
        LOG_API_CHANNEL,
        f"#Set_{tutorial_key.title()}_Video\n\n"
        f"ɢʀᴏᴜᴘ ɴᴀᴍᴇ : {title}\n"
        f"ɢʀᴏᴜᴘ ɪᴅ : {grp_id}\n"
        f"ɪɴᴠɪᴛᴇ ʟɪɴᴋ : {invite_link}\n"
        f"ᴜᴘᴅᴀᴛᴇᴅ ʙʏ : {message.from_user.mention()}"
    )

async def handle_shortner_command(c, m, shortner_key, api_key, log_prefix, fallback_url, fallback_api):
    grp_id = m.chat.id
    if not await is_check_admin(c, grp_id, m.from_user.id):
        return await m.reply_text(script.ADMIN_ALRT_TXT)
    if len(m.command) != 3:
        return await m.reply(
            f"<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ʟɪᴋᴇ -\n\n`/{m.command[0]} domain your_api_key`</b>"
        )
    sts = await m.reply("<b>♻️ ᴄʜᴇᴄᴋɪɴɢ...</b>")
    await asyncio.sleep(1.2)
    await sts.delete()
    if m.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await m.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    try:
        URL = m.command[1]
        API = m.command[2]
        await save_group_settings(grp_id, shortner_key, URL)
        await save_group_settings(grp_id, api_key, API)
        await m.reply_text(f"<b><u>✅ sʜᴏʀᴛɴᴇʀ ᴀᴅᴅᴇᴅ</u>\n\nꜱɪᴛᴇ - `{URL}`\nᴀᴘɪ - `{API}`</b>")
        user_id = m.from_user.id
        user_info = f"@{m.from_user.username}" if m.from_user.username else f"{m.from_user.mention}"
        link = (await c.get_chat(m.chat.id)).invite_link
        grp_link = f"[{m.chat.title}]({link})"
        log_message = (
            f"#{log_prefix}\n\nɴᴀᴍᴇ - {user_info}\n\nɪᴅ - `{user_id}`"
            f"\n\nꜱɪᴛᴇ - {URL}\n\nᴀᴘɪ - `{API}`"
            f"\n\nɢʀᴏᴜᴘ - {grp_link}\nɢʀᴏᴜᴘ ɪᴅ - `{grp_id}`"
        )
        await c.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)
    except Exception as e:
        await save_group_settings(grp_id, shortner_key, fallback_url)
        await save_group_settings(grp_id, api_key, fallback_api)
        await m.reply_text(
            f"<b><u>💢 ᴇʀʀᴏʀ ᴏᴄᴄᴜʀᴇᴅ!</u>\n\n"
            f"ᴅᴇꜰᴀᴜʟᴛ ꜱʜᴏʀᴛɴᴇʀ ᴀᴘᴘʟɪᴇᴅ\n"
            f"ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄʜᴀɴɢᴇ ᴛʀʏ ᴀ ᴠᴀʟɪᴅ ꜱɪᴛᴇ ᴀɴᴅ ᴀᴘɪ ᴋᴇʏ.\n\n"
            f"ʟɪᴋᴇ:\n\n`/{m.command[0]} domain your_api_key`\n\n"
            f"💔 ᴇʀʀᴏʀ - <code>{e}</code></b>"
        )

@Client.on_message(filters.command('verify'))
async def set_verify(c, m):
    await handle_shortner_command(c, m, 'shortner', 'api', 'New_Shortner_Set_For_1st_Verify', SHORTENER_WEBSITE, SHORTENER_API)

@Client.on_message(filters.command('verify2'))
async def set_verify_2(c, m):
    await handle_shortner_command(c, m, 'shortner_two', 'api_two', 'New_Shortner_Set_For_2nd_Verify', SHORTENER_WEBSITE2, SHORTENER_API2)

@Client.on_message(filters.command('verify3'))
async def set_verify_3(c, m):
    await handle_shortner_command(c, m, 'shortner_three', 'api_three', 'New_Shortner_Set_For_3rd_Verify', SHORTENER_WEBSITE3, SHORTENER_API3)

@Client.on_message(filters.command('log'))
async def set_log(client, message):
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text(script.ADMIN_ALRT_TXT)
    if len(message.text.split()) == 1:
        await message.reply("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ʟɪᴋᴇ ᴛʜɪꜱ - \n\n`/log -100******`</b>")
        return
    sts = await message.reply("<b>♻️ ᴄʜᴇᴄᴋɪɴɢ...</b>")
    await asyncio.sleep(1.2)
    await sts.delete()
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    try:
        log = int(message.text.split(" ", 1)[1])
    except IndexError:
        return await message.reply_text("<b><u>ɪɴᴠᴀɪʟᴅ ꜰᴏʀᴍᴀᴛ!!</u>\n\nᴜsᴇ ʟɪᴋᴇ ᴛʜɪs - `/log -100xxxxxxxx`</b>")
    except ValueError:
        return await message.reply_text('<b>ᴍᴀᴋᴇ sᴜʀᴇ ɪᴅ ɪs ɪɴᴛᴇɢᴇʀ...</b>')
    try:
        t = await client.send_message(chat_id=log, text="<b>ʜᴇʏ ᴡʜᴀᴛ's ᴜᴘ!!</b>")
        await asyncio.sleep(3)
        await t.delete()
    except Exception as e:
        return await message.reply_text(f'<b><u>😐 ᴍᴀᴋᴇ sᴜʀᴇ ᴛʜɪs ʙᴏᴛ ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ...</u>\n\n💔 ᴇʀʀᴏʀ - <code>{e}</code></b>')
    await save_group_settings(grp_id, 'log', log)
    await message.reply_text(f"<b>✅ sᴜᴄᴄᴇssꜰᴜʟʟʏ sᴇᴛ ʏᴏᴜʀ ʟᴏɢ ᴄʜᴀɴɴᴇʟ ꜰᴏʀ {title}\n\nɪᴅ - `{log}`</b>", disable_web_page_preview=True)
    user_id = message.from_user.id
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"{message.from_user.mention}"
    link = (await client.get_chat(message.chat.id)).invite_link
    grp_link = f"[{message.chat.title}]({link})"
    log_message = f"#New_Log_Channel_Set\n\nɴᴀᴍᴇ - {user_info}\n\nɪᴅ - `{user_id}`\n\nʟᴏɢ ᴄʜᴀɴɴᴇʟ ɪᴅ - `{log}`\nɢʀᴏᴜᴘ ʟɪɴᴋ - `{grp_link}`\n\nɢʀᴏᴜᴘ ɪᴅ : `{grp_id}`"
    await client.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True) 

@Client.on_message(filters.command('time2'))
async def set_time_2(client, message):
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")       
    grp_id = message.chat.id
    title = message.chat.title
    invite_link = await client.export_chat_invite_link(grp_id)
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text(script.ADMIN_ALRT_TXT)
    try:
        time = int(message.text.split(" ", 1)[1])
    except:
        return await message.reply_text("<b>ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ\n\nᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ʟɪᴋᴇ ᴛʜɪꜱ - <code>/time2 600</code> [ ᴛɪᴍᴇ ᴍᴜꜱᴛ ʙᴇ ɪɴ ꜱᴇᴄᴏɴᴅꜱ ]</b>")   
    await save_group_settings(grp_id, 'verify_time', time)
    await message.reply_text(f"<b>✅️ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴇᴛ 2ɴᴅ ᴠᴇʀɪꜰʏ ᴛɪᴍᴇ ꜰᴏʀ {title}\n\nᴛɪᴍᴇ - <code>{time}</code></b>")
    await client.send_message(LOG_API_CHANNEL, f"#Set_2nd_Verify_Time\n\nɢʀᴏᴜᴘ ɴᴀᴍᴇ : {title}\n\nɢʀᴏᴜᴘ ɪᴅ : {grp_id}\n\nɪɴᴠɪᴛᴇ ʟɪɴᴋ : {invite_link}\n\nᴜᴘᴅᴀᴛᴇᴅ ʙʏ : {message.from_user.username}")

@Client.on_message(filters.command('time3'))
async def set_time_3(client, message):
    chat_type = message.chat.type
    if chat_type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")       
    grp_id = message.chat.id
    title = message.chat.title
    invite_link = await client.export_chat_invite_link(grp_id)
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text(script.ADMIN_ALRT_TXT)
    try:
        time = int(message.text.split(" ", 1)[1])
    except:
        return await message.reply_text("<b>ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ\n\nᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ʟɪᴋᴇ ᴛʜɪꜱ - <code>/time3 3600</code> [ ᴛɪᴍᴇ ᴍᴜꜱᴛ ʙᴇ ɪɴ ꜱᴇᴄᴏɴᴅꜱ ]</b>")   
    await save_group_settings(grp_id, 'third_verify_time', time)
    await message.reply_text(f"<b>✅️ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴇᴛ 3ʀᴅ ᴠᴇʀɪꜰʏ ᴛɪᴍᴇ ꜰᴏʀ {title}\n\nᴛɪᴍᴇ - <code>{time}</code></b>")
    await client.send_message(LOG_API_CHANNEL, f"#Set_3rd_Verify_Time\n\nɢʀᴏᴜᴘ ɴᴀᴍᴇ : {title}\n\nɢʀᴏᴜᴘ ɪᴅ : {grp_id}\n\nɪɴᴠɪᴛᴇ ʟɪɴᴋ : {invite_link}\n\nᴜᴘᴅᴀᴛᴇᴅ ʙʏ : {message.from_user.username}")

@Client.on_message(filters.command('details'))
async def all_settings(client, message):
    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply_text("<b>ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪɴ ɢʀᴏᴜᴘ...</b>")
    grp_id = message.chat.id
    title = message.chat.title
    if not await is_check_admin(client, grp_id, message.from_user.id):
        return await message.reply_text(script.ADMIN_ALRT_TXT)
    try:
        settings = await get_settings(grp_id)
    except Exception as e:
        return await message.reply_text(f"<b>⚠️ ᴇʀʀᴏʀ ꜰᴇᴛᴄʜɪɴɢ ꜱᴇᴛᴛɪɴɢꜱ:</b>\n<code>{e}</code>")
    text = generate_settings_text(settings, title)
    btn = [
        [InlineKeyboardButton("♻️ ʀᴇꜱᴇᴛ ꜱᴇᴛᴛɪɴɢꜱ", callback_data=f"reset_group_{grp_id}")],
        [InlineKeyboardButton("🚫 ᴄʟᴏꜱᴇ", callback_data="close_data")]
    ]
    dlt = await message.reply_text(text, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True)
    await asyncio.sleep(300)
    await dlt.delete()

@Client.on_callback_query(filters.regex(r"^reset_group_(\-\d+)$"))
async def reset_group_callback(client, callback_query):
    grp_id = int(callback_query.matches[0].group(1))
    user_id = callback_query.from_user.id
    if not await is_check_admin(client, grp_id, user_id):
        return await callback_query.answer(script.ADMIN_ALRT_TXT, show_alert=True)
    await callback_query.answer("♻️ ʀᴇꜱᴇᴛᴛɪɴɢ ꜱᴇᴛᴛɪɴɢꜱ...")
    defaults = {
        'shortner': SHORTENER_WEBSITE,
        'api': SHORTENER_API,
        'shortner_two': SHORTENER_WEBSITE2,
        'api_two': SHORTENER_API2,
        'shortner_three': SHORTENER_WEBSITE3,
        'api_three': SHORTENER_API3,
        'verify_time': TWO_VERIFY_GAP,
        'third_verify_time': THREE_VERIFY_GAP,
        'template': IMDB_TEMPLATE,
        'tutorial': TUTORIAL,
        'tutorial_2': TUTORIAL_2,
        'tutorial_3': TUTORIAL_3,
        'caption': FILE_CAPTION,
        'log': LOG_CHANNEL,
        'is_verify': IS_VERIFY,
        'fsub': AUTH_CHANNELS
    }
    current = await get_settings(grp_id)
    if current == defaults:
        return await callback_query.answer("✅ ꜱᴇᴛᴛɪɴɢꜱ ᴀʟʀᴇᴀᴅʏ ᴅᴇꜰᴀᴜʟᴛ.", show_alert=True)
    for key, value in defaults.items():
        await save_group_settings(grp_id, key, value)
    updated = await get_settings(grp_id)
    title = callback_query.message.chat.title
    text = generate_settings_text(updated, title, reset_done=True)
    buttons = [
        [InlineKeyboardButton("♻️ ʀᴇꜱᴇᴛ ꜱᴇᴛᴛɪɴɢꜱ", callback_data=f"reset_group_{grp_id}")],
        [InlineKeyboardButton("🚫 ᴄʟᴏꜱᴇ", callback_data="close_data")]
    ]
    await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

@Client.on_message(filters.command("verify") & filters.user(ADMINS))
async def verify(bot, message):
    try:
        chat_type = message.chat.type
        if chat_type == enums.ChatType.PRIVATE:
            return await message.reply_text("ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋs ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘs!")
        if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grpid = message.chat.id
            title = message.chat.title
            command_text = message.text.split(' ')[1] if len(message.text.split(' ')) > 1 else None
            if command_text == "off":
                await save_group_settings(grpid, 'is_verify', False)
                return await message.reply_text("✓ ᴠᴇʀɪꜰʏ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅɪsᴀʙʟᴇᴅ.")
            elif command_text == "on":
                await save_group_settings(grpid, 'is_verify', True)
                return await message.reply_text("✗ ᴠᴇʀɪꜰʏ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴇɴᴀʙʟᴇᴅ.")
            else:
                return await message.reply_text("ʜɪ, ᴛᴏ ᴇɴᴀʙʟᴇ ᴠᴇʀɪꜰʏ, ᴜsᴇ <code>/verify on</code> ᴀɴᴅ ᴛᴏ ᴅɪsᴀʙʟᴇ ᴠᴇʀɪꜰʏ, ᴜsᴇ <code>/verify off</code>.")
    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text(f"Error: {e}")

@Client.on_message(filters.command('fsub'))
async def set_fsub(client, message):
    try:
        userid = message.from_user.id if message.from_user else None
        if not userid:
            return await message.reply("ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            return await message.reply_text("ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴜsᴇᴅ ɪɴ ɢʀᴏᴜᴘs")
        grp_id = message.chat.id
        title = message.chat.title
        if not await is_check_admin(client, grp_id, userid):
            return await message.reply_text(script.ADMIN_ALRT_TXT)
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            return await message.reply_text("ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ!\n\nᴄᴀɴ ᴀᴅᴅ ᴍᴜʟᴛɪᴘʟᴇ ᴄʜᴀɴɴᴇʟs sᴇᴘᴀʀᴀᴛᴇᴅ ʙʏ sᴘᴀᴄᴇs.\n\nʟɪᴋᴇ: /fsub ɪᴅ𝟷 ɪᴅ𝟸 ɪᴅ𝟹")
        option = args[1].strip()
        try:
            fsub_ids = [int(x) for x in option.split()]
        except ValueError:
            return await message.reply_text('ᴍᴀᴋᴇ sᴜʀᴇ ᴀʟʟ ɪᴅs ᴀʀᴇ ɪɴᴛᴇɢᴇʀs.')
        if len(fsub_ids) > 5:
            return await message.reply_text("ᴍᴀxɪᴍᴜᴍ 5 ᴄʜᴀɴɴᴇʟs ᴀʟʟᴏᴡᴇᴅ.")
        channels = "ᴄʜᴀɴɴᴇʟs:\n"
        channel_titles = []
        for id in fsub_ids:
            try:
                chat = await client.get_chat(id)
            except Exception as e:
                return await message.reply_text(f"{id} ɪs ɪɴᴠᴀʟɪᴅ!\nᴍᴀᴋᴇ sᴜʀᴇ ᴛʜɪs ʙᴏᴛ ɪs ᴀᴅᴍɪɴ ɪɴ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.\n\nError - {e}")
            if chat.type != enums.ChatType.CHANNEL:
                return await message.reply_text(f"{id} ɪs ɴᴏᴛ ᴀ ᴄʜᴀɴɴᴇʟ.")
            channel_titles.append(f"{chat.title} (`{id}`)")
            channels += f'{chat.title}\n'
        await save_group_settings(grp_id, 'fsub', fsub_ids)
        await message.reply_text(f"sᴜᴄᴄᴇssғᴜʟʟʏ sᴇᴛ ꜰꜱᴜʙ ᴄʜᴀɴɴᴇʟ(ꜱ) ꜰᴏʀ {title} ᴛᴏ\n\n{channels}")
        mention = message.from_user.mention if message.from_user else "Unknown"
        await client.send_message(LOG_API_CHANNEL, f"#ꜰꜱᴜʙ_ꜱᴇᴛ\n\nᴜꜱᴇʀ - {mention} ꜱᴇᴛ ᴛʜᴇ ꜰᴏʀᴄᴇ ᴄʜᴀɴɴᴇʟ(ꜱ) ꜰᴏʀ {title}:\n\nꜰꜱᴜʙ ᴄʜᴀɴɴᴇʟ(ꜱ):\n" + '\n'.join(channel_titles))
    except Exception as e:
        err_text = f"⚠️ Error in fSub :\n{e}"
        logger.error(err_text)
        await client.send_message(LOG_API_CHANNEL, err_text)

@Client.on_message(filters.command('nofsub'))
async def nofsub(client, message):
    try:
        user = message.from_user
        if not user:
            return await message.reply("ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ ʏᴏᴜ ᴄᴀɴ'ᴛ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
        if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            return await message.reply_text("ᴛʜɪs ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴜsᴇᴅ ɪɴ ɢʀᴏᴜᴘs.")
        grp_id = message.chat.id
        title = message.chat.title
        if not await is_check_admin(client, grp_id, user.id):
            return await message.reply_text(script.ADMIN_ALRT_TXT)
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            return await message.reply_text("ᴜsᴀɢᴇ:\n\n• <code>/nofsub all</code>→ ʀᴇᴍᴏᴠᴇ ᴀʟʟ ꜰsᴜʙ ᴄʜᴀɴɴᴇʟs\n• <code>/nofsub</code> ɪᴅ𝟷 ɪᴅ𝟸 ... → ʀᴇᴍᴏᴠᴇ sᴘᴇᴄɪꜰɪᴄ ᴄʜᴀɴɴᴇʟ ɪᴅs")
        option = args[1].strip()
        settings = await get_settings(grp_id)
        cr_fsubs = settings.get("fsub", []) if settings else []
        if not cr_fsubs:
            return await message.reply_text("ɴᴏ ꜰsᴜʙ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ sᴇᴛ ꜰᴏʀ ᴛʜɪs ɢʀᴏᴜᴘ.")
        if option.lower() == "all":
            await save_group_settings(grp_id, 'fsub', [])
            await message.reply_text(f"✅ ᴀʟʟ ꜰsᴜʙ ᴄʜᴀɴɴᴇʟs ʀᴇᴍᴏᴠᴇᴅ ꜰᴏʀ {title}")
            return await client.send_message(LOG_API_CHANNEL, f"#ꜰsᴜʙ_ʀᴇᴍᴏᴠᴇᴅ\n\n👤 {user.mention} ʀᴇᴍᴏᴠᴇᴅ ᴀʟʟ ꜰsᴜʙ ᴄʜᴀɴɴᴇʟs ꜰᴏʀ {title}")
        try:
            remove_ids = [int(x) for x in option.split()]
        except ValueError:
            return await message.reply_text("ᴍᴀᴋᴇ sᴜʀᴇ ᴀʟʟ ɪᴅs ᴀʀᴇ ᴠᴀʟɪᴅ ɪɴᴛᴇɢᴇʀs.")
        new_fsubs = [cid for cid in cr_fsubs if cid not in remove_ids]
        r_id = [cid for cid in cr_fsubs if cid in remove_ids]
        if not r_id:
            return await message.reply_text("ɴᴏɴᴇ ᴏꜰ ᴛʜᴇ ɢɪᴠᴇɴ ɪᴅs ᴡᴇʀᴇ ꜰᴏᴜɴᴅ ɪɴ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ꜰsᴜʙ ʟɪsᴛ.")
        await save_group_settings(grp_id, 'fsub', new_fsubs)
        r_t = []
        for cid in r_id:
            try:
                chat = await client.get_chat(cid)
                r_t.append(f"• {chat.title} ({cid})")
            except:
                r_t.append(f"• ᴜɴᴋɴᴏᴡɴ ({cid})")
        await message.reply_text(
            f"✅ ʀᴇᴍᴏᴠᴇᴅ {len(r_id)} ꜰsᴜʙ ᴄʜᴀɴɴᴇʟ(s) ꜰʀᴏᴍ {title}:\n" +
            "\n".join(r_t)
        )

        await client.send_message(
            LOG_API_CHANNEL,
            f"#ꜰsᴜʙ_ʀᴇᴍᴏᴠᴇᴅ\n\n👤 {user.mention} ʀᴇᴍᴏᴠᴇᴅ ꜰsᴜʙ ᴄʜᴀɴɴᴇʟ(s) ꜰʀᴏᴍ {title}:\n" +
            "\n".join(r_t)
        )
    except Exception as e:
        print(f"[ERROR] nofsub: {e}")
        await message.reply_text(f"⚠️ ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀᴇᴅ: {e}")

@Client.on_message(filters.private & filters.command("resetgroup") & filters.user(ADMINS))
async def reset_all_settings(client, message):
    try:
        reset_count = await db.reset_settings()
        await message.reply_text(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜱᴇᴛᴛɪɴɢꜱ ꜰᴏʀ  <code>{reset_count}</code> ɢʀᴏᴜᴘꜱ. ᴅᴇꜰᴀᴜʟᴛ ᴠᴀʟᴜᴇꜱ ᴡɪʟʟ ʙᴇ ᴜꜱᴇᴅ ✅</b>", quote=True)
    except Exception as e:
        print(f"[ERROR] reset_all_settings: {e}")
        await message.reply_text("<b>🚫 An error occurred while resetting group settings.\nPlease try again later.</b>", quote=True)

@Client.on_message(filters.command("trial_reset") & filters.user(ADMINS))
async def reset_trial(client, message):
    try:
        if len(message.command) > 1:
            target_user_id = int(message.command[1])
            updated_count = await db.reset_free_trial(target_user_id)
            message_text = f"ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʀᴇꜱᴇᴛ ꜰʀᴇᴇ ᴛʀᴀɪʟ ꜰᴏʀ ᴜꜱᴇʀꜱ {target_user_id}." if updated_count else f"ᴜꜱᴇʀ {target_user_id} ɴᴏᴛ ꜰᴏᴜɴᴅ ᴏʀ ᴅᴏɴ'ᴛ ᴄʟᴀɪᴍ ꜰʀᴇᴇ ᴛʀᴀɪʟ ʏᴇᴛ."
        else:
            updated_count = await db.reset_free_trial()
            message_text = f"ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʀᴇꜱᴇᴛ ꜰʀᴇᴇ ᴛʀᴀɪʟ ꜰᴏʀ {updated_count} ᴜꜱᴇʀꜱ."
        await message.reply_text(message_text)
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")

@Client.on_message(filters.command("resetlimit") & filters.user(ADMINS))
async def reset_limit_command(_, message):
    try:
        args = message.text.split()
        if len(args) < 2:
            return await message.reply_text("🧭 ᴜꜱᴀɢᴇ:\n\n• <code>/resetlimit all</code> – ʀᴇꜱᴇᴛ ᴀʟʟ ᴜꜱᴇʀꜱ’ ʟɪᴍɪᴛꜱ\n• <code>/resetlimit</code> ᴜꜱᴇʀ_ɪᴅ – ʀᴇꜱᴇᴛ ꜰᴏʀ ᴀ ꜱᴘᴇᴄɪꜰɪᴄ ᴜꜱᴇʀ")
        option = args[1].lower()
        if option == "all":
            await db.reset_file_count()
            return await message.reply_text("♻️ ᴀʟʟ ᴜꜱᴇʀꜱ’ ꜰɪʟᴇ ʟɪᴍɪᴛꜱ ʜᴀᴠᴇ ʙᴇᴇɴ ʀᴇꜱᴇᴛ.")
        try:
            user_id = int(option)
        except ValueError:
            return await message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ. ɪᴛ ᴍᴜꜱᴛ ʙᴇ ᴀ ɴᴜᴍʙᴇʀ.")
        user = await db.col.find_one({"id": user_id})
        if not user:
            return await message.reply_text(f"❌ ɴᴏ ᴜꜱᴇʀ ꜰᴏᴜɴᴅ ᴡɪᴛʜ ɪᴅ <code>{user_id}</code>")
        await db.reset_file_count(user_id)
        return await message.reply_text("✅ ꜰɪʟᴇ ʟɪᴍɪᴛ ʀᴇꜱᴇᴛ ꜰᴏʀ ᴜꜱᴇʀ.")
    except Exception as e:
        await message.reply_text(f"❌ ᴇʀʀᴏʀ: <code>{e}</code>")

@Client.on_message(filters.command("checklimit") & filters.user(ADMINS))
async def check_limit_command(_, message):
    try:
        args = message.text.split()
        if len(args) != 2:
            return await message.reply_text("🧭 ᴜꜱᴀɢᴇ:\n\n» <code>/checklimit</code> ᴜsᴇʀ_ɪᴅ - ᴄʜᴇᴄᴋ ᴜsᴇʀ ʟɪᴍɪᴛ")
        try:
            user_id = int(args[1])
        except ValueError:
            return await message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ. ɪᴛ ᴍᴜꜱᴛ ʙᴇ ᴀ ɴᴜᴍʙᴇʀ.")
        count = await db.get_user_file_count(user_id)
        return await message.reply_text(f"📊 ᴜsᴇʀ <code>{user_id}</code> ʜᴀs ᴜsᴇᴅ {count}/{FILES_LIMIT} ꜰɪʟᴇs.")
    except Exception as e:
        await message.reply_text(f"❌ ᴇʀʀᴏʀ: <code>{e}</code>")
