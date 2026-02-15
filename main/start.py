import time 
import math
import os
import asyncio 
import pyrogram
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message 
from config import API_ID, API_HASH, ERROR_MESSAGE, LOGIN_SYSTEM, STRING_SESSION, CHANNEL_ID, WAITING_TIME
from database.db import db
from .strings import HELP_TXT, SETTING_HELP_TXT
from bot import RazzeshUser
from config import ADMINS
from PIL import Image

class batch_temp(object):
    IS_BATCH = {}

# download status
async def downstatus(client, statusfile, message, chat, file_num):
    while True:
        if os.path.exists(statusfile): break
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        try:
            if not os.path.exists(statusfile):  # ✅ Double check
                break
            
            with open(statusfile, "r") as f:
                txt = f.read()
            
            if os.path.exists(statusfile):  # ✅ Check before using
                try:
                    await client.edit_message_text(chat, message.id, f"📥 **Downloading File No {file_num}...**\n\n{txt}")
                except:
                    pass
            
            await asyncio.sleep(10)
        except FileNotFoundError:  # ✅ Gracefully exit
            break    
        except Exception:
            await asyncio.sleep(5)

# upload status
async def upstatus(client, statusfile, message, chat, file_num):
    while True:
        if os.path.exists(statusfile): 
            break
        await asyncio.sleep(3)      
    while os.path.exists(statusfile):
        try:
            if not os.path.exists(statusfile):  # ✅ Check first
                break
            
            with open(statusfile, "r") as f:
                txt = f.read()
            
            try:
                await client.edit_message_text(chat, message.id, f"📤 **Uploading File No {file_num}...**\n\n{txt}")
            except:
                pass
            
            await asyncio.sleep(10)
        except FileNotFoundError:  # ✅ Handle gracefully
            break
        except Exception:
            await asyncio.sleep(5)


# start command
@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    print("DEBUG: Start command received!")
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    
    # Using a high-quality GIF URL
    START_GIF = "https://c.tenor.com/HXvyLMZcw_8AAAAC/tenor.gif" 

    # Optimized Layout for Mobile Responsiveness
    buttons = [
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings_home")],
        [InlineKeyboardButton("❣️ Developer", url="https://t.me/razzeshhere")],
        [
            InlineKeyboardButton('🔍 Support', url='https://t.me/theheropirate'),
            InlineKeyboardButton('🤖 Updates', url='https://t.me/thekillerpirate')
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(buttons)

    await client.send_animation(
        chat_id=message.chat.id,
        animation=START_GIF,
        caption=f"<b>👋 Hi {message.from_user.mention}, I am Save Restricted Content Bot.\n\nI can send you restricted content by its post link.\n\nFor downloading restricted content /login first.\n\nKnow how to use bot by - /help</b>",
        reply_markup=reply_markup,
        reply_to_message_id=message.id
    )
    return

#stream command
@Client.on_message(filters.command("stream") & filters.private)
async def cinema_mode(client, message):
    if len(message.command) < 2:
        return await message.reply("⚠️ **Usage:** `/stream [Link]`")
        
    link = message.command[1]
    
    try:
        # --- 1. PARSE THE LINK ---
        if "https://t.me/c/" in link:
            # Private Link format: https://t.me/c/123456789/101
            # We need to add "-100" to the chat ID part
            datas = link.split("/")
            chat_id = int("-100" + datas[4])
            msg_id = int(datas[5].split("?")[0]) # Handle ?single if present
            
        elif "https://t.me/" in link:
            # Public Link format: https://t.me/channelname/101
            datas = link.split("/")
            chat_id = datas[3] # Username remains a string for public chats
            msg_id = int(datas[4].split("?")[0])
        else:
            return await message.reply("❌ **Invalid Telegram Link.**")

        # --- 2. GENERATE STREAM LINK ---
        # ⚠️ IMPORTANT: Replace 127.0.0.1 with your VPS Public IP if deploying!
        # If running locally for testing, 127.0.0.1 is fine.
        host = "http://16.171.168.163:8000" 
        
        watch_link = f"{host}/watch/{chat_id}/{msg_id}"
        
        await message.reply(
            "🎬 **Cinema Mode Ready**\n\n"
            f"Click to watch instantly (No Download needed):\n"
            f"🔗 [Open Player]({watch_link})",
            disable_web_page_preview=True
        )
        
    except Exception as e:
        await message.reply(f"⚠️ **Error parsing link:** {e}")


#settings command
@Client.on_callback_query(filters.regex("settings_home"))
async def settings_menu(client, callback_query):
    user_id = callback_query.from_user.id
    idx_status = await db.get_batch_index_status(user_id)
    idx_text = "✅ On" if idx_status else "❌ Off"
    buttons = [[
        InlineKeyboardButton("📝 Set Custom Caption", callback_data="set_caption_action")
      ],[
          InlineKeyboardButton("🖼️ Custom Thumbnail", callback_data="set_thumb_action")
      ],[
		InlineKeyboardButton("📤 Customized Upload", callback_data="set_upload_action")
	  ],[
          InlineKeyboardButton("⚡ Parallel Batch", callback_data="parallel_settings")
      ],[
          InlineKeyboardButton(f"🗂️ Batch Index: {idx_text}", callback_data="toggle_batch_index")
      ],[
        InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_start")
    ]]
    await callback_query.message.edit_text(
        "**⚙️ Bot Settings**\n\nChoose an option below to customize your experience:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, callback_query):
    # This recreates your main menu buttons from the start command
    buttons = [
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings_home")],
        [InlineKeyboardButton("❣️ Developer", url="https://t.me/razzeshhere")],
        [
            InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/theheropirate'),
            InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/thekillerpirate')
        ]
    ]
    await callback_query.message.edit_text(
        text=f"<b>👋 Hi {callback_query.from_user.mention}, I am Save Restricted Content Bot.\n\nI can send you restricted content by its post link.\n\nFor downloading restricted content /login first.\n\nKnow how to use bot by - /help</b>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
#set_caption
@Client.on_callback_query(filters.regex("set_caption_action"))
async def set_caption_process(client, callback_query):
    buttons = [
        [InlineKeyboardButton("📝 Single Caption (Apply to All)", callback_data="cap_mode_single")],
        [InlineKeyboardButton("🔢 Batch Caption (Sequence)", callback_data="cap_mode_batch")],
        [InlineKeyboardButton("🔙 Back", callback_data="settings_home")]
    ]
    await callback_query.message.edit_text(
        "**📝 Custom Caption Setup**\n\n"
        "Choose how you want to caption your files:\n\n"
        "**1. Single Caption:** One caption applied to every file in the batch.\n"
        "**2. Batch Caption:** A specific list of captions for each file (e.g., Ep 1, Ep 2...).",
        reply_markup=InlineKeyboardMarkup(buttons)
    ) 

@Client.on_callback_query(filters.regex("cap_mode_single"))
async def cap_mode_single(client, callback_query):
    user_id = callback_query.from_user.id
    await db.set_status(user_id, "awaiting_caption_single")
    await callback_query.message.edit_text(
        "**📝 Set Single Caption**\n\n"
        "Send the caption you want to use for **ALL** files.\n\n"
        "• `{caption}` - Keep original text.\n"
        "• `off` - Disable custom captions.\n"
        "• `/cancel` - Cancel."
    )

@Client.on_callback_query(filters.regex("cap_mode_batch"))
async def cap_mode_batch(client, callback_query):
    user_id = callback_query.from_user.id
    await db.set_status(user_id, "awaiting_caption_batch")
    await callback_query.message.edit_text(
        "**🔢 Set Batch Caption**\n\n"
        "Send a list of captions separated by `///`.\n\n"
        "**Format:** `Caption 1///Caption 2///Caption 3`\n\n"
        "**💡 Logic:**\n"
        "• The bot applies them in order: File 1 gets Caption 1, File 2 gets Caption 2.\n"
        "• If you have 20 files but only 3 captions, files 4-20 will use their original caption.\n"
        "• **Tip:** Ask an AI: *'Write a list of captions for [Course Name] separated by ///'*.\n\n"
        "**⚠️ Note:** This list is ONE-TIME use. It clears after the batch finishes."
    )    

#custom thumbnail callback
THUMB_RETRIES = {}

@Client.on_callback_query(filters.regex("set_thumb_action"))
async def set_thumb_process(client, callback_query):
    user_id = callback_query.from_user.id
    
    # Reset retries when entering mode
    THUMB_RETRIES[user_id] = 0
    
    await db.set_status(user_id, "awaiting_custom_thumb")
    await callback_query.message.edit_text(
        "**🖼️ Custom Thumbnail Setup**\n\n"
        "Send the **Photo** you want to use as the thumbnail for all videos.\n\n"
        "• Format: `.jpg` or `.png` (Send as Photo, not File)\n"
        "• Type `off` to delete your custom thumbnail.\n"
        "• Type `/cancel` to abort.\n\n"
        "**⚠️ Note:** You have 2 attempts to send a valid image."
    )	

#customized upload
@Client.on_callback_query(filters.regex("set_upload_action"))
async def set_upload_process(client, callback_query):
    user_id = callback_query.from_user.id
    await db.set_status(user_id, "awaiting_upload_id")
    await callback_query.message.edit_text(
        "**📤 Customized Upload Settings**\n\n"
        "Send the **Channel or Group ID** where you want your files delivered.\n\n"
        "• Use the format `-100xxxxxxxxx`.\n"
        "• Make sure the bot is an **Admin** in that chat.\n\n"
        "Type `off` to use personal chat or `/cancel` to abort."
    )
	
#batch callbacks command
@Client.on_callback_query(filters.regex("batch_count"))
async def cb_count(client, cb):
    """Triggered when user clicks 'Message Count' button"""
    await db.set_status(cb.from_user.id, "awaiting_batch_count")
    await cb.message.edit_text(
        "🔢 **Batch by Message Count**\n\n"
        "Please enter how many messages you want to process (1-100).\n\n"
        "• Bot will start from your initial link and go forward.\n"
        "• Send only an integer (number)."
    )

@Client.on_callback_query(filters.regex("batch_endlink"))
async def cb_endlink(client, cb):
    """Triggered when user clicks 'End Post Link' button"""
    await db.set_status(cb.from_user.id, "awaiting_end_link")
    await cb.message.edit_text(
        "🔗 **Batch by End Post Link**\n\n"
        "Please send the **End Post Link**.\n\n"
        "• This link must be from the **same channel** as the start link.\n"
        "• Range limit is 100 messages."
    )

@Client.on_callback_query(filters.regex("parallel_settings"))
async def parallel_settings(client, callback_query):
    user_id = callback_query.from_user.id
    status = await db.get_parallel_status(user_id)
    status_text = "🟢 **ON**" if status else "🔴 **OFF**"
    
    buttons = [[
        InlineKeyboardButton("✅ ON", callback_data="parallel_on"),
        InlineKeyboardButton("❌ OFF", callback_data="parallel_off")
    ], [InlineKeyboardButton("🔙 Back", callback_data="settings_home")]]
    
    await callback_query.message.edit_text(
        f"⚡ **Parallel Batch Download**\n\n"
        f"**Current Status:** {status_text}\n\n"
        "When **ON**, the bot downloads the next file while the previous one uploads.\n"
        "Maximum 1 Download + 1 Upload at a time.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("parallel_on|parallel_off"))
async def parallel_toggle(client, callback_query):
    is_on = callback_query.data == "parallel_on"
    await db.set_parallel_status(callback_query.from_user.id, is_on)
    await callback_query.answer(f"Parallel Batch: {'Enabled' if is_on else 'Disabled'}")
    await parallel_settings(client, callback_query)    

# --- NEW CALLBACK FOR TOGGLE ---
@Client.on_callback_query(filters.regex("toggle_batch_index"))
async def toggle_batch_index(client, callback_query):
    user_id = callback_query.from_user.id
    current_status = await db.get_batch_index_status(user_id)
    
    # Flip the switch
    new_status = not current_status
    await db.set_batch_index_status(user_id, new_status)
    
    await callback_query.answer(f"Batch Index {'Enabled' if new_status else 'Disabled'}")
    # Refresh the menu to show new icon
    await settings_menu(client, callback_query)    
	
# help command
@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await client.send_message(
        chat_id=message.chat.id, 
        text=f"{HELP_TXT}"
    )

# setting_help command
@Client.on_message(filters.command(["settinghelp"]))
async def send_setting_help(client: Client, message: Message):
    await client.send_message(
        chat_id=message.chat.id, 
        text=f"{SETTING_HELP_TXT}"
    )    
	
#batch command 
@Client.on_message(filters.command("batch") & filters.private)
async def batch_cmd(client, message):
    user_id = message.from_user.id
    from config import ADMINS
    
    is_premium = await db.is_premium(user_id)
    
    if not is_premium and user_id != ADMINS:
        return await message.reply(
            "⭐ **Premium Feature**\n\nBatch mode is only available for premium users.\nPlease contact the owner.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❣️ Contact Owner", url="https://t.me/razzeshhere")]])
        )
    
    await db.set_status(user_id, "choosing_batch_filter")
    
    buttons = [
        [InlineKeyboardButton("All 🌐", callback_data="filter_all")],
        [
            InlineKeyboardButton("Video 🎥", callback_data="filter_video"), 
            InlineKeyboardButton("Photos 📸", callback_data="filter_photo")
        ],
        [
            InlineKeyboardButton("Document 📄", callback_data="filter_document"), 
            InlineKeyboardButton("Audio 🎵", callback_data="filter_audio")
        ],
        [
            InlineKeyboardButton("Animation/GIF 🎞", callback_data="filter_animation")
        ]
    ]
    
    await message.reply(
        "🛠 **Batch Configuration**\n\nSelect the specific file type you want to extract:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

#filter batch command
@Client.on_callback_query(filters.regex(r"^filter_"))
async def set_batch_filter_callback(client, callback_query):
    user_id = callback_query.from_user.id
    selected_filter = callback_query.data.split("_")[1]
    
    await db.set_batch_data(user_id, {"link": None, "retries": 0, "filter": selected_filter})
    await db.set_status(user_id, "awaiting_start_link")
    
    await callback_query.message.edit_text(
        f"✅ **Filter Set to:** `{selected_filter.capitalize()}`\n\n"
        "📦 **Batch Mode**\n\nPlease send the **Starting Post Link**.\n\n"
        "• You have **2 attempts** to provide a valid link.\n• Type `/cancel` to abort."
    )    

#add user ID for owner -
@Client.on_message(filters.command("add") & filters.user(ADMINS))
async def add_premium(client, message):
    if len(message.command) < 2:
        return await message.reply("⚠️ **Usage:** `/add USER_ID`")
    
    try:
        user_id = int(message.text.split(" ")[1])
        await db.add_premium_user(user_id)
        await message.reply(f"✅ **User `{user_id}` has been added to Premium!**")
    except ValueError:
        await message.reply("❌ **Invalid User ID. Please send a number.**")

# --- 1. REMOVE PREMIUM COMMAND ---
@Client.on_message(filters.command("remove") & filters.user(ADMINS))
async def remove_premium(client, message):
    if len(message.command) < 2:
        return await message.reply("⚠️ **Usage:** `/remove USER_ID`")
    
    try:
        user_id = int(message.text.split(" ")[1])
        
        # Check if user was actually premium before removing (Optional but good UX)
        if await db.is_premium(user_id):
            await db.remove_premium_user(user_id)
            await message.reply(f"❌ **User `{user_id}` has been removed from Premium.**")
        else:
            await message.reply(f"ℹ️ **User `{user_id}` was not a premium user.**")
            
    except ValueError:
        await message.reply("❌ **Invalid User ID. Please send a number.**")

# ---STATS BOX ---
@Client.on_message(filters.command("stats") & filters.user(ADMINS))
async def get_stats(client, message):
    start_time = time.time()
    # Fetching data
    msg = await message.reply("🔄 **Fetching Statistics...**")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 2)
    total_users = await db.count_all_users()
    premium_users = await db.count_premium_users()
    free_users = total_users - premium_users
    
    # The "Box Type" Design
    stats_text = (
        "╭─── [ 📊 **SYSTEM STATUS** ] ───╮\n"
        "│\n"
        f"│  👥  **Total Users** : `{total_users}`\n"
        f"│  👑  **Premium** : `{premium_users}`\n"
        f"│  👤  **Free Users** : `{free_users}`\n"
        "│\n"
        "╰──────────────────────────╯\n\n"
        f"⚡ **Ping:** `{ping_time}ms`"
    )
    
    await msg.edit(stats_text)     

# --- Users List View ---
def format_user_list(user_list, title):
    text = f"📋 **{title}**\n\n"
    for i, user in enumerate(user_list, 1):
        uid = user.get('id')
        if uid is None:
            temp_id = user.get('_id')
            if isinstance(temp_id, int):
                uid = temp_id
            else:
                uid = "No Integer ID Found"

        # 2. NAME & USERNAME FETCHING
        name = user.get('name', user.get('first_name', 'Unknown Name'))
        username = user.get('username', None)
        
        # 3. CONSTRUCT THE LINE
        user_line = f"{i}. 👤 **{name}** "
        if username:
            user_line += f"(@{username}) "
        
        user_line += f"[`{uid}`]\n"
        text += user_line
        
    return text

# --- /listfree & /listpremium Commands ---
@Client.on_message(filters.command(["listfree", "listpremium"]) & filters.user(ADMINS))
async def list_users_handler(client, message):
    msg = await message.reply("🔄 **Sorting Database... Please Wait.**")
    
    # 1. Fetch all raw data
    all_users_cursor = await db.get_all_users_list()
    premium_ids = await db.get_premium_user_ids()
    
    # Debug print to console (optional, helps verify IDs)
    print(f"DEBUG: Found {len(premium_ids)} premium IDs: {premium_ids}")

    # 2. Create a "Lookup Table" prioritizing the TELEGRAM ID
    user_map = {}
    for user in all_users_cursor:
        # 🛑 CRITICAL FIX: Look for 'id' first!
        # Only use '_id' if 'id' is missing.
        uid = user.get('id') 
        if uid is None:
            uid = user.get('_id')
            
        # Store user in map with the CLEAN ID as the key
        if uid:
            user_map[uid] = user

    premium_list = []
    free_list = []

    # 3. BUILD PREMIUM LIST (The Intersection)
    for pid in premium_ids:
        if pid in user_map:
            # User is in both lists -> Add to Premium View
            premium_list.append(user_map[pid])
        else:
            # User is Premium but hasn't started bot -> Add Placeholder
            premium_list.append({'id': pid, 'name': '⚠️ Unknown (Manually Added)', 'username': None})

    # 4. BUILD FREE LIST (The Remainder)
    for uid, user in user_map.items():
        if uid not in premium_ids:
            free_list.append(user)
            
    # 5. Determine which list to show
    command = message.command[0]
    if command == "listpremium":
        final_list = premium_list
        title = "Premium Users List"
    else:
        final_list = free_list
        title = "Free Users List"
        
    if not final_list:
        return await msg.edit(f"📂 **{title} is empty.**")

    # 6. Output Generation
    output_text = format_user_list(final_list, title)
    
    if len(output_text) > 4000:
        filename = f"{command}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(output_text.replace("**", "").replace("`", ""))
        
        await msg.delete()
        await message.reply_document(
            document=filename,
            caption=f"📂 **{title}**\n\n⚠️ List too long for text message. Sending file.",
            file_name=filename
        )
        os.remove(filename)
    else:
        await msg.edit(output_text)       

# cancel command
@Client.on_message(filters.command(["cancel"]))
async def send_cancel(client, message):
    user_id = message.from_user.id
    
    try:
        # 1. Check if user actually has a batch running
        status = await db.get_status(user_id)
        
        if status is None or status == "cancelled":
            await message.reply("**⚠️ No active batch to cancel.**")
            message.stop_propagation()
            return
        
        # 2. Set status to signal cancellation
        await db.set_status(user_id, "cancelled")
        
        # 3. Set batch flag to prevent new tasks
        batch_temp.IS_BATCH[user_id] = True
        
        # 4. Send confirmation
        if status == "processing_batch":
            # Batch message
            await message.reply(
                "**🛑 Batch Cancellation Requested!**\n\n"
                "Stopping ongoing batch processing...\n"
                "Please wait 5 seconds before starting again."
            )
        elif status == "processing_single":
            # Single file message ✅ NEW
            await message.reply(
                "**🛑 File Transfer Cancelled!**\n\n"
                "Please wait 5 seconds before starting again."
            )
        else:
            # Generic message
            await message.reply(
                "**✅ Operation Cancelled!**\n\n"
                "Please wait 5 seconds before starting again."
            )
        
    except Exception as e:
        await message.reply(f"**⚠️ Cancellation Error:** {str(e)}")
    
    # ✅ CRITICAL: Stop propagation BEFORE return
    message.stop_propagation()
    
    # ✅ CRITICAL: Return to exit
    return	
	
# The Catcher function
@Client.on_message((filters.text | filters.photo) & filters.private, group=-1)
async def handle_user_states(client, message):
    user_id = message.from_user.id
    status = await db.get_status(user_id)

    # --- Section 1: Handle Custom Caption States ---
    if status == "awaiting_caption_single":
        if message.text.lower() == "/cancel":
            await db.set_status(user_id, None)
            
            # --- PAST LOGIC: CLEANUP (Preserved) ---
            up_log = f"{message.id}upstatus.txt"
            down_log = f"{message.id}downstatus.txt"
            
            if os.path.exists(up_log) or os.path.exists(down_log):
                try:
                    # Clear logs and files
                    for f in [up_log, down_log]:
                        if os.path.exists(f): 
                            os.remove(f)
                    if os.path.exists("downloads"):
                        for file in os.listdir("downloads"):
                            if str(message.id) in file:
                                os.remove(os.path.join("downloads", file))
                    await message.reply("**✅ Active process stopped and storage cleared.**")
                except Exception as e:
                    print(f"Cleanup Error: {e}")
            else:
                await message.reply("**✅ Single caption setup cancelled.**")
            
            message.stop_propagation()
            return

        elif message.text.lower() == "off":
            await db.set_custom_caption(user_id, "off")
            await db.set_caption_mode(user_id, "single") # Reset mode
            await db.set_status(user_id, None)
            await message.reply("**❌ Custom caption disabled.**")
            message.stop_propagation()
            return
        else:
            await db.set_custom_caption(user_id, message.text)
            await db.set_caption_mode(user_id, "single") # Set mode
            await db.set_status(user_id, None)
            await message.reply("**✅ Single Caption Saved!**\nThis will apply to all future files.")
            message.stop_propagation()
            return

    elif status == "awaiting_caption_batch":
        if message.text.lower() == "/cancel":
            await db.set_status(user_id, None)
            
            # --- PAST LOGIC: CLEANUP (Preserved) ---
            up_log = f"{message.id}upstatus.txt"
            down_log = f"{message.id}downstatus.txt"
            
            if os.path.exists(up_log) or os.path.exists(down_log):
                try:
                    for f in [up_log, down_log]:
                        if os.path.exists(f): 
                            os.remove(f)
                    if os.path.exists("downloads"):
                        for file in os.listdir("downloads"):
                            if str(message.id) in file:
                                os.remove(os.path.join("downloads", file))
                    await message.reply("**✅ Active process stopped and storage cleared.**")
                except Exception as e:
                    print(f"Cleanup Error: {e}")
            else:
                await message.reply("**✅ Batch caption setup cancelled.**")

            message.stop_propagation()
            return

        # Validate format (Just a warning, we still save it)
        if "///" not in message.text and len(message.text) < 50:
             await message.reply("⚠️ **Warning:** No separators (`///`) found. This will look like a single caption. Continue? (Send new text to override or /cancel)")
        
        await db.set_custom_caption(user_id, message.text)
        await db.set_caption_mode(user_id, "batch") # Set mode
        await db.set_status(user_id, None)
        await message.reply(
            "**✅ Batch Captions Queued!**\n\n"
            "These will be used for your **next batch only** and then cleared."
        )
        message.stop_propagation()
        return
			
	# --- NEW SECTION 2: Batch Start Link Controller ---
    elif status == "awaiting_start_link":
        if message.text.lower() == "/cancel":
            await db.set_status(user_id, None)
            return await message.reply("✅ **Batch mode cancelled.**")

        batch_data = await db.get_batch_data(user_id)
        link = message.text.strip()
        
        # Validation Logic
        if "t.me/" in link:
            batch_data["link"] = link
            batch_data["retries"] = 0 # Reset retries on success
            await db.set_batch_data(user_id, batch_data)
            await db.set_status(user_id, "choosing_batch_type")
            
            buttons = [
                [
                    InlineKeyboardButton("🔢 Message Count", callback_data="batch_count"),
                    InlineKeyboardButton("🔗 End Post Link", callback_data="batch_endlink")
                ]
            ]
            await message.reply(
                "✅ **Start Link Saved.**\n\nHow do you want to define the batch range?", 
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            # Retry Logic (The "2-try" system)
            batch_data["retries"] += 1
            if batch_data["retries"] >= 2:
                await db.set_status(user_id, None)
                await message.reply("❌ **Too many invalid attempts.** Exiting Batch Mode.")
                message.stop_propagation()				
            else:
                await db.set_batch_data(user_id, batch_data)
                await message.reply(f"⚠️ **Invalid Link.** Please try again ({2 - batch_data['retries']} attempts left).")
        
        message.stop_propagation()
        return
		
    # --- Section 3: Handle Customized Upload States ---
    elif status == "awaiting_upload_id":
        if message.text.lower() == "/cancel":
            await db.set_status(user_id, None)
            
            # Heavy Cleanup only if an active process log exists
            up_log = f"{message.id}upstatus.txt"
            down_log = f"{message.id}downstatus.txt"
            
            if os.path.exists(up_log) or os.path.exists(down_log):
                try:
                    for f in [up_log, down_log]:
                        if os.path.exists(f): 
                            os.remove(f)
                    if os.path.exists("downloads"):
                        for file in os.listdir("downloads"):
                            if str(message.id) in file:
                                os.remove(os.path.join("downloads", file))
                    await message.reply("**✅ Active process stopped and storage cleared.**")
                except Exception as e:
                    print(f"Cleanup Error: {e}")
            else:
                await message.reply("**✅ Upload destination menu cancelled.**")

            message.stop_propagation()
            return

        elif message.text.lower() == "off":
            await db.set_custom_upload(user_id, "off")
            await db.set_status(user_id, None)
            await message.reply("**❌ Customized Upload disabled. Delivering to DM.**")
            message.stop_propagation()
            return
        else:
            try:
                target_id = int(message.text.strip())
                await db.set_custom_upload(user_id, target_id)
                await db.set_status(user_id, None)
                await message.reply(f"**✅ Destination set to `{target_id}`!**")
            except ValueError:
                return await message.reply("Invalid ID. Send a number starting with `-100`.")
            
            message.stop_propagation()
            return

# --- Section 4: Final Batch Range Processing ---
    elif status == "awaiting_batch_count":
        if batch_temp.IS_BATCH.get(user_id) == False:
            return await message.reply("⚠️ **Please wait!** The previous batch is still shutting down. Try again in 5 seconds.")
            
        try:
            count = int(message.text.strip())
            if 1 <= count <= 100:
                # 1. Update status to 'processing' immediately to prevent race condition
                await db.set_status(user_id, "processing_batch") 
                
                batch_data = await db.get_batch_data(user_id)

                # 2. Initialize session (The connection delay helps DB sync)
                if LOGIN_SYSTEM == True:
                    user_data = await db.get_session(user_id)
                    api_id = int(await db.get_api_id(user_id))
                    api_hash = await db.get_api_hash(user_id)
                    
                    # Prevent Collision
                    safe_username = message.from_user.username or "NoUsername"
                    session_name = f"session_{user_id}_{safe_username}"
                    
                    acc = Client(session_name, session_string=user_data, api_hash=api_hash, api_id=api_id)
                    await acc.connect()
                else:
                    acc = RazzeshUser

                # 3. Call helper with the active session
                await run_batch(client, acc, message, batch_data["link"], count=count)
            else:
                await db.set_status(user_id, None)
                await message.reply("❌ **Error:** Message count must be between 1-100.")
        except ValueError:
            await db.set_status(user_id, None)
            await message.reply("❌ **Error:** Please send a valid integer.")
        
        message.stop_propagation()
        return

    elif status == "awaiting_end_link":		
        if batch_temp.IS_BATCH.get(user_id) == False:
            return await message.reply("⚠️ **Please wait!** The previous batch is still shutting down. Try again in 5 seconds.")
            
        start_link_data = await db.get_batch_data(user_id)
        start_link = start_link_data["link"]
        end_link = message.text.strip()
        
        # Validation: Same channel check
        if "t.me/" not in end_link or start_link.split('/')[-2] != end_link.split('/')[-2]:
            await db.set_status(user_id, None)
            await message.reply("❌ **Error:** Links must be from the same channel.")
            message.stop_propagation()
            return
           
        try:
            start_id = int(start_link.split('/')[-1])
            end_id = int(end_link.split('/')[-1])
            
            if end_id < start_id:
                await db.set_status(user_id, None)
                await message.reply("❌ **Error:** End link cannot be older than the start link.")
                message.stop_propagation() 
                return

            count = (end_id - start_id) + 1
            if count > 100:
                count = 100
                await message.reply("⚠️ **Warning:** Range exceeds 100. Processing first 100 files only.")
            
            # Initialize session locally
            if LOGIN_SYSTEM == True:
                user_data = await db.get_session(user_id)
                api_id = int(await db.get_api_id(user_id))
                api_hash = await db.get_api_hash(user_id)
                
                # Prevent Collision
                safe_username = message.from_user.username or "NoUsername"
                session_name = f"session_{user_id}_{safe_username}"
                
                acc = Client(session_name, session_string=user_data, api_hash=api_hash, api_id=api_id)
                await acc.connect()
            else:
                acc = RazzeshUser

            await db.set_status(user_id, "processing_batch")
            await run_batch(client, acc, message, start_link, count=count)		
            
        except Exception as e:
            await db.set_status(user_id, None)
            await message.reply(f"❌ **Error:** {str(e)}")			
            
        message.stop_propagation()
        return
    
# --- Section: Handle Custom Thumbnail ---
    elif status == "awaiting_custom_thumb":
        # 1. ESCAPE ROUTE (/cancel)
        if message.text and message.text.lower() == "/cancel":
            await db.set_status(user_id, None)
            THUMB_RETRIES.pop(user_id, None)
            await message.reply("**✅ Thumbnail setup cancelled.**")
            return

        # 2. DELETE/OFF COMMAND (.delete or off)
        if message.text and (message.text.lower() == ".delete" or message.text.lower() == "off"):
            await db.delete_custom_thumb(user_id) # Clears the DB field
            await db.set_status(user_id, None)
            THUMB_RETRIES.pop(user_id, None)
            await message.reply("**🗑️ Custom thumbnail deleted.**\nYour videos will now use their original thumbnails.")
            return

        # 3. SET/REPLACE THUMBNAIL (Send Photo)
        if message.photo:
            # Telegram sends multiple sizes; we take the last one (largest high-res)
            file_id = message.photo.file_id
            
            # This automatically REPLACES any old thumb in the DB
            await db.set_custom_thumb(user_id, file_id)
            
            await db.set_status(user_id, None)
            THUMB_RETRIES.pop(user_id, None)
            await message.reply(
                "**✅ Custom Thumbnail Saved!**\n\n"
                "• This image will replace the original thumbnail for all future files.\n"
                "• To remove it, go to Settings -> Custom Thumbnail and type `.delete`."
            )
            return
        
        # 4. INVALID INPUT HANDLING (2 Tries)
        else:
            current_try = THUMB_RETRIES.get(user_id, 0) + 1
            THUMB_RETRIES[user_id] = current_try
            
            if current_try >= 2:
                await db.set_status(user_id, None)
                THUMB_RETRIES.pop(user_id, None)
                await message.reply("**❌ Too many invalid attempts.** Exiting Thumbnail Mode.")
            else:
                await message.reply(f"⚠️ **Invalid Format!**\n\nPlease send a **Photo** to set a thumbnail, or type `.delete` to remove the existing one.\n\nAttempts left: {2 - current_try}")
            return
        
#save function 
@Client.on_message(filters.text & filters.private, group=1)
async def save(client: Client, message: Message):
    user_id = message.from_user.id
    
    # 1. THE GATEKEEPER: Check if user is busy with a menu or setup
    status = await db.get_status(user_id)
    if status is not None and status != "processing_batch":
        return      
    
    # Joining chat
    if ("https://t.me/+" in message.text or "https://t.me/joinchat/" in message.text) and LOGIN_SYSTEM == False:
        if RazzeshUser is None:
            await client.send_message(message.chat.id, "String Session is not Set", reply_to_message_id=message.id)
            return
        try:
            try:
                await RazzeshUser.join_chat(message.text)
            except Exception as e: 
                await client.send_message(message.chat.id, f"Error : {e}", reply_to_message_id=message.id)
                return
            await client.send_message(message.chat.id, "Chat Joined", reply_to_message_id=message.id)
        except UserAlreadyParticipant:
            await client.send_message(message.chat.id, "Chat already Joined", reply_to_message_id=message.id)
        except InviteHashExpired:
            await client.send_message(message.chat.id, "Invalid Link", reply_to_message_id=message.id)
        return
    
    if "https://t.me/" in message.text:
        # Check if a task is already processing to prevent storage overload
        if batch_temp.IS_BATCH.get(message.from_user.id) == False:
            return await message.reply_text("**One Task Is Already Processing. Wait For Complete It. If You Want To Cancel This Task Then Use - /cancel**")

        # Session Initialization Logic
        if LOGIN_SYSTEM == True:
            user_id = message.from_user.id
            user_data = await db.get_session(user_id)
            if user_data is None:
                await message.reply("**For Downloading Restricted Content You Have To /login First.**")
                return
            api_id = int(await db.get_api_id(user_id))
            api_hash = await db.get_api_hash(user_id)
            try:
                # Prevent Collision
                safe_username = message.from_user.username or "NoUsername"
                session_name = f"session_{user_id}_{safe_username}"
                
                acc = Client(session_name, session_string=user_data, api_hash=api_hash, api_id=api_id)
                await acc.connect()
            except:
                return await message.reply("**Your Login Session Expired. So /logout First Then Login Again By - /login**")
        else:
            if RazzeshUser is None:
                await client.send_message(message.chat.id, f"**String Session is not Set**", reply_to_message_id=message.id)
                return
            acc = RazzeshUser
                
        # Lock batch status for this user
        batch_temp.IS_BATCH[message.from_user.id] = False

        # Parse the link and extract the single Message ID
        datas = message.text.split("/")
        msgid = int(datas[-1].replace("?single","").split("-")[0])

        await db.set_status(message.from_user.id, "processing_single")

        try:
            # --- Logic for Different Link Types ---
            
            # 1. Private Channel Link
            if "https://t.me/c/" in message.text:
                chatid = int("-100" + datas[4])
                try:
                    await handle_private(client, acc, message, chatid, msgid)
                except Exception as e:
                    if ERROR_MESSAGE == True:
                        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
        
            # 2. Bot/Private Chat Link
            elif "https://t.me/b/" in message.text:
                username = datas[4]
                try:
                    await handle_private(client, acc, message, username, msgid)
                except Exception as e:
                    if ERROR_MESSAGE == True:
                        await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)
                
            # 3. Public Channel Link
            else:
                username = datas[3]
                try:
                    # Try copying directly first for public links
                    msg = await client.get_messages(username, msgid)
                    await client.copy_message(message.chat.id, msg.chat.id, msg.id, reply_to_message_id=message.id)
                except Exception:
                    # If copy fails, fall back to handle_private session
                    try:                
                        await handle_private(client, acc, message, username, msgid)               
                    except Exception as e:
                        if ERROR_MESSAGE == True:
                            await client.send_message(message.chat.id, f"Error: {e}", reply_to_message_id=message.id)

        finally:
            await db.set_status(message.from_user.id, None)

            # Wait time between tasks
            await asyncio.sleep(WAITING_TIME)

            # Disconnect session if LOGIN_SYSTEM is active
            if LOGIN_SYSTEM == True:
                try:
                    await acc.disconnect()
                except:
                    pass                        
            
            # Unlock batch status for next task
            batch_temp.IS_BATCH[message.from_user.id] = True

#upload worker 
async def upload_worker(client, acc, message, upload_queue, stats_msg, total_count, index_list):
    user_id = message.from_user.id
    while True:
        data = await upload_queue.get()
        if data is None: # Shutdown signal
            break

        status = await db.get_status(user_id)
        if status == "cancelled":
            upload_queue.task_done()
            continue # Skip this file
        
        file_path, file_num, start_time, chat_id, msg_id = data
        try:
            sent_msg = await handle_private(client, acc, message, chat_id, msg_id, start_time, file_num, upload_only_file=file_path)
            
            # --- DATA RECORDING FOR INDEX ---
            if sent_msg:
                final_caption = sent_msg.caption if sent_msg.caption else f"File {file_num}"
                display_name = final_caption.split('\n')[0][:50] 
                
                # 2. Add to Shared List (Thread Safe enough for append)
                index_list.append({
                    "num": file_num,
                    "id": sent_msg.id,
                    "name": display_name,
                    "link": sent_msg.link if sent_msg.link else f"https://t.me/c/{str(user_id)[4:] if str(user_id).startswith('-100') else user_id}/{sent_msg.id}"
                })
            await asyncio.sleep(0.8)
            
            new_status = await db.get_status(user_id)
            if new_status == "processing_batch":
                await stats_msg.edit_text(f"📊 **Batch Progress:** {file_num}/{total_count} files processed.")
            else:
                print(f"DEBUG [Worker]: Cancellation verified. UI overwrite blocked for File {file_num}")  
                return  
        except Exception as e:
            if "STOP_TRANSMISSION" in str(e):
                return
        finally:
            upload_queue.task_done()
            

# run batch helper function
async def run_batch(client, bot_acc, message, start_link, count):
    user_id = message.from_user.id
    base_id = int(start_link.split('/')[-1])
    chat_id = start_link.split('/')[-2]
    batch_start_time = time.time()
    batch_data = await db.get_batch_data(user_id)
    user_filter = batch_data.get("filter", "all")
    
    if chat_id.isdigit():
        chat_id = int("-100" + chat_id)

    # --- 🛠️ STEP 1: INITIALIZE PRIVATE SESSION ---
    if LOGIN_SYSTEM == True:
        user_data = await db.get_session(user_id)
        api_id = int(await db.get_api_id(user_id))
        api_hash = await db.get_api_hash(user_id)
        
        # Create a unique session name to prevent collision on EC2
        safe_username = message.from_user.username or "NoUsername"
        session_name = f"session_{user_id}_{safe_username}"
        
        # Create the private client for THIS specific batch
        acc = Client(session_name, session_string=user_data, api_hash=api_hash, api_id=api_id)
        await acc.connect()
        
        # --- 🛠️ STEP 2: PEER HANDSHAKE ---
        try:
            # Force the session to "see" the channel and cache its Access Hash
            await acc.get_chat(chat_id) 
        except Exception as e:
            print(f"Handshake error: {e}")
    else:
        # Fallback to the global bot/string session if login is off
        acc = bot_acc

    index_list = []
    # 1. INITIALIZE RAILWAY TRACKS
    # The Queue acts as the 'buffer' between download and upload lanes
    upload_queue = asyncio.Queue(maxsize=1) 
    parallel_on = await db.get_parallel_status(user_id) 
    
    stats_msg = await message.reply(f"📊 **Batch Started:** 0/{count} files processed.")
    
    # 2. START THE UPLOAD WORKER (TRACK 2)
    uploader = asyncio.create_task(upload_worker(client, acc, message, upload_queue, stats_msg, count, index_list))
    
    try:
        await db.set_status(user_id, "processing_batch")
        batch_temp.IS_BATCH[user_id] = False

        for i in range(count):
            file_num = i + 1
            current_msg_id = base_id + i

            # 3. FIRST-FILE SYNC & 4S RAILWAY COOLDOWN
            if i == 0: 
                await asyncio.sleep(2)
            else:
                await asyncio.sleep(4) 
                
            # 4. PRE-TRANSFER CANCEL CHECK
            current_status = await db.get_status(user_id)
            if current_status != "processing_batch":
                if not uploader.done():
                    uploader.cancel()
                await asyncio.sleep(1.2)
                await stats_msg.edit_text(f"🛑 **Batch Cancelled!** Processed {i-1}/{count} files.")
                break 

            try:
                # 5. DOWNLOAD LANE (TRACK 1)
                # 'download_only=True' tells handle_private to stop after saving the file
                file_path = await handle_private(client, acc, message, chat_id, current_msg_id, batch_start_time, file_num, download_only=True, user_filter=user_filter)
                
                if file_path == "SKIPPED":
                    if file_num % 5 == 0 or file_num == count:
                        try:
                            await stats_msg.edit_text(f"📊 **Batch Progress:** {file_num}/{count} files parsed.\n⏭️ Skipped file (Filter applied).")
                        except: pass
                    continue
                
                if file_path and file_path != "SKIPPED" and os.path.exists(file_path):
                    # 6. FEED THE UPLOAD LANE
                    if parallel_on:
                        # Parallel: Put in queue and immediately start next download cooldown
                        await upload_queue.put((file_path, file_num, time.time(), chat_id, current_msg_id))
                    else:
                        # Sequential: Put in queue and wait for it to be processed
                        await upload_queue.put((file_path, file_num, time.time(), chat_id, current_msg_id))
                        await upload_queue.join() 
                
            except Exception as e:
                # 7. MID-TRANSFER KILL SWITCH
                if "STOP_TRANSMISSION" in str(e):
                    # Kill worker
                    if not uploader.done(): 
                        uploader.cancel()
                    
                    await asyncio.sleep(1)
                    await stats_msg.edit_text(f"🛑 **Batch Cancelled!** Processed {i}/{count} files.")
                    return 
                else:
                    print(f"Batch Item Error: {e}")
                    continue
        
        await upload_queue.put(None) 
        await uploader
        #-----BATCH INDEX------
        if await db.get_batch_index_status(user_id):
            index_list.sort(key=lambda x: x['num'])
            index_text = "🗂️ **Batch Index**\n\n"
            temp_text = index_text
            
            for item in index_list:
                # Format: [File Name](Link)
                line = f"{item['num']}. [{item['name']}]({item['link']})\n"
                
                # 4096 Char Limit Check (Overflow Valve)
                if len(temp_text) + len(line) > 4000:
                    await message.reply(temp_text, disable_web_page_preview=True)
                    temp_text = "🗂️ **Batch Index (Cont.)**\n\n" + line
                else:
                    temp_text += line
            if len(temp_text) > len("🗂️ **Batch Index (Cont.)**\n\n"):
                await message.reply(temp_text, disable_web_page_preview=True)

        final_status = await db.get_status(user_id)
        if final_status == "cancelled":
             await stats_msg.reply("🛑 **Batch Cancelled !!.**")
        else:
             await stats_msg.reply("✅ **Batch Processing Complete!**")
    finally:
        # 9. CLEAN UP STATE AND SESSION
        if await db.get_caption_mode(user_id) == "batch":
            await db.set_custom_caption(user_id, "off") # Wipe the complex string
            await db.set_caption_mode(user_id, "single") # Reset to safe default
            print(f"DEBUG: Batch captions cleared for user {user_id}")


        await asyncio.sleep(2)
        batch_temp.IS_BATCH[user_id] = True
        current = await db.get_status(user_id)
        if current != "cancelled":
            await db.set_status(user_id, None)
        if LOGIN_SYSTEM == True:
            try:
                await acc.disconnect()
            except:
                pass

#clock function
def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    # Define time increments: 60s, 60m, 24h
    periods = [('h', 3600), ('m', 60), ('s', 1)]
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            up_time += f"{period_value}{period_name} "
    return up_time.strip() if up_time else "0s"


#cancel check and progress function
async def progress(current, total, message, type, user_id, db, start_time, file_num):
    status = await db.get_status(user_id)
    if status is not None and status not in ["processing_batch", "processing_single"]:
        print(f"DEBUG [Exit]: STOP_TRANSMISSION triggered for File {file_num}")
        raise Exception("STOP_TRANSMISSION")
    
    now = time.time()
    diff = now - start_time
    tmp = "📊 **Calculating Speed and ETA...**"

    # Update every 10 seconds to stay within Telegram limits
    if round(diff % 15.00) == 0 or current == total:
        percentage = current * 100 / total
        
        # 1. Speed Calculation
        speed_bytes = current / diff if diff > 0 else 0
        speed_mb = speed_bytes / (1024 * 1024)
        
        # 2. Correct ETA Logic (Remaining Data / Speed)
        remaining_bytes = total - current
        eta_seconds = round(remaining_bytes / speed_bytes) if speed_bytes > 0 else 0
        
        # 3. Use our new Human-Readable time formatter
        elapsed = get_readable_time(round(diff))
        estimated = get_readable_time(eta_seconds)
        
        progress_bar = "".join(["🟧" for i in range(math.floor(percentage / 10))])
        remaining_bar = "".join(["⬜️" for i in range(10 - math.floor(percentage / 10))])
        
        tmp = (
            f"✨ {progress_bar}{remaining_bar}\n\n"
            f"🔋 **Percentage •** {percentage:.1f}%\n"
            f"🚀 **Speed •** {speed_mb:.2f} MB/s\n"
            f"🚦 **Size •** {current / (1024 * 1024):.1f} MB / {total / (1024 * 1024):.1f} MB\n"
            f"⏰ **ETA •** {estimated}\n"
            f"⌛️ **Elapsed •** {elapsed}"
        )
        
        try:
        # Use a local variable for ID to prevent NoneType during the 'raise' period
            msg_id = getattr(message, 'id', None)
            if msg_id:
                status_file = f'{msg_id}{type}.txt'
                with open(status_file, "w", encoding='utf-8') as fileup:
                    fileup.write(tmp)
                    
                if current == total:
                    await asyncio.sleep(1)
        except AttributeError as e:
            print(f"DEBUG [AttributeError]: {e} | Type: {type(message)}")
            pass
        except Exception as e:
            print(f"DEBUG [General]: {e}")
            pass
        
# handle private
async def handle_private(client: Client, acc, message: Message, chatid: int, msgid: int, batch_time=None, file_num=1, download_only=False, upload_only_file=None, user_filter="all"):
    msg: Message = await acc.get_messages(chatid, msgid)
    if msg.empty: return 
    msg_type = get_message_type(msg)
    if not msg_type: 
            if user_filter != "all":
                return "SKIPPED" 
            return 
    if user_filter != "all":
        if user_filter == "audio" and msg_type.lower() in ["audio", "voice"]:
            pass 
        elif msg_type.lower() != user_filter:
            return "SKIPPED"

    # Define targets
    user_id = message.from_user.id
    user_chat = message.chat.id
    log_chat = int(CHANNEL_ID) if CHANNEL_ID else None
    if upload_only_file:
        file = upload_only_file
        goto_upload = True 
        msg: Message = await acc.get_messages(chatid, msgid)
    else:
        goto_upload = False
        msg: Message = await acc.get_messages(chatid, msgid)

    # Check for Customized Upload preference
    custom_destination = await db.get_custom_upload(user_id)

    if custom_destination and str(custom_destination).lower() != "off":
        try:
            await client.get_chat_member(custom_destination, "me")
            chat = custom_destination
        except Exception:
            await client.send_message(user_chat, "**⚠️ Error:** I cannot access your custom channel. **Uploading to personal chat instead.**")
            chat = user_chat
    else:
        chat = user_chat

    if not goto_upload:
        if "Text" == msg_type:
            try:
                await client.send_message(chat, msg.text, entities=msg.entities, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)
                return 
            except Exception as e:
                if ERROR_MESSAGE:
                    await client.send_message(user_chat, f"Error: {e}", reply_to_message_id=message.id)
                return 

        smsg = await client.send_message(user_chat, '📥 **Preparing Download...**', reply_to_message_id=message.id)
        asyncio.create_task(downstatus(client, f'{message.id}_{file_num}_down.txt', smsg, user_chat, file_num))

        try:
            start_time = batch_time if batch_time else time.time()
            file = await acc.download_media(
                msg, 
                progress=progress, 
                progress_args=[message, f"_{file_num}_down", user_id, db, start_time, file_num]
            )
            if os.path.exists(f'{message.id}_{file_num}_down.txt'):
                os.remove(f'{message.id}_{file_num}_down.txt')

            check_status = await db.get_status(user_id)
            if check_status == "cancelled":
                if os.path.exists(file): os.remove(file)
                await smsg.edit("🛑 **Download Halted. Process Terminated.**")
                return    
            
            try:
                await smsg.edit(f"✅ **Download No {file_num} Finished!**\n📦 **Track 1:** Station clear.\n🚀 **Track 2:** Handing over to Upload Lane...")
            except:
                pass

            if download_only:
                # Create a background task to delete the message after 4 seconds
                async def delete_smsg_delayed():
                    await asyncio.sleep(4)
                    try:
                        await smsg.delete()
                    except:
                        pass
                
                asyncio.create_task(delete_smsg_delayed())
                return file    
        except Exception as e:
            if str(e) == "STOP_TRANSMISSION":
                await smsg.edit("**🛑 Batch Stopped Mid-Download.**")
                return
            elif ERROR_MESSAGE:
                await client.send_message(user_chat, f"Error: {e}", reply_to_message_id=message.id) 
            if os.path.exists(f'{message.id}_{file_num}_down.txt'):
                os.remove(f'{message.id}_{file_num}_down.txt')
            return await smsg.delete()
        
    check_status = await db.get_status(user_id)
    if check_status == "cancelled":
        if 'file' in locals() and os.path.exists(file): os.remove(file)
        return    

    if goto_upload:
        smsg = await client.send_message(user_chat, '📤 **Preparing Upload...**', reply_to_message_id=message.id) 
    asyncio.create_task(upstatus(client, f'{message.id}_{file_num}_up.txt', smsg, user_chat, file_num))

    user_custom = await db.get_custom_caption(user_id)
    caption_mode = await db.get_caption_mode(user_id) #
    original_caption = msg.caption if msg.caption else ""
    
    final_caption = original_caption # Default fallback

    if user_custom and user_custom.lower() != "off":
        
        # MODE 1: SINGLE CAPTION
        if caption_mode == "single":
            final_caption = user_custom.replace("{caption}", original_caption) if "{caption}" in user_custom else user_custom
            
        # MODE 2: BATCH CAPTION (The CNC Feed)
        elif caption_mode == "batch":
            captions_list = user_custom.split("///")
            list_index = file_num - 1 
            
            if list_index < len(captions_list):
                raw_cap = captions_list[list_index].strip()
                if raw_cap: 
                    final_caption = raw_cap
                else:
                    final_caption = original_caption
            else:
                final_caption = original_caption
    
    caption = final_caption
    sent_msg = None

    # --- THUMBNAIL PROCESSING ENGINE ---
    custom_thumb_id = await db.get_custom_thumb(user_id)
    final_thumb_path = None
    
    # 1. Check if user wants a custom thumb
    if custom_thumb_id:
        try:
            # Download user's custom image
            custom_thumb_path = await client.download_media(custom_thumb_id, file_name=f"thumb_{file_num}.jpg")
            
            # 2. Determine Original Dimensions (The "Force Attach" Logic)
            target_width = 320 # Default fallback
            target_height = 180 
            
            if "Video" == msg_type:
                target_width = msg.video.width
                target_height = msg.video.height
            elif "Document" == msg_type and msg.document.thumbs:
                 # Try to get from thumb if doc has one
                 target_width = msg.document.thumbs[0].width
                 target_height = msg.document.thumbs[0].height

            # 3. Resize using Pillow (CNC Precision)
            if custom_thumb_path:
                img = Image.open(custom_thumb_path)
                img = img.resize((target_width, target_height))
                img.save(custom_thumb_path) # Overwrite with resized version
                final_thumb_path = custom_thumb_path
                
        except Exception as e:
            print(f"Thumbnail Error: {e}")
            final_thumb_path = None # Fallback to original

    # --- Unified Upload Logic with Kill Switch ---
    try:
        if await db.get_status(user_id) == "cancelled":
             raise Exception("STOP_TRANSMISSION")
        start_time = batch_time if batch_time else time.time()
        if "Document" == msg_type:
            try:
                ph_path = await acc.download_media(msg.document.thumbs[0].file_id)
            except:
                ph_path = None
            sent_msg = await client.send_document(
                chat, file, thumb=ph_path, caption=caption, 
                reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, 
                progress=progress, progress_args=[message, f"_{file_num}_up", user_id, db, start_time, file_num]
            )
            if ph_path: os.remove(ph_path)

        elif "Video" == msg_type:
            if final_thumb_path:
                ph_path = final_thumb_path
            else:
                try:
                    ph_path = await acc.download_media(msg.video.thumbs[0].file_id)
                except:
                    ph_path = None   
            sent_msg = await client.send_video(
                chat, file, duration=msg.video.duration, width=target_width if 'target_width' in locals() else msg.video.width,
            height=target_height if 'target_height' in locals() else msg.video.height, thumb=ph_path, caption=caption, 
                reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, 
                progress=progress, progress_args=[message, f"_{file_num}_up", user_id, db, start_time, file_num]
            )
            if ph_path: os.remove(ph_path)

        elif "Audio" == msg_type:
            try:
                ph_path = await acc.download_media(msg.audio.thumbs[0].file_id)
            except:
                ph_path = None
            sent_msg = await client.send_audio(
                chat, file, thumb=ph_path, caption=caption, 
                reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, 
                progress=progress, progress_args=[message, f"_{file_num}_up", user_id, db, start_time, file_num]
            )
            if ph_path: os.remove(ph_path)

        elif "Animation" == msg_type:
            sent_msg = await client.send_animation(chat, file, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

        elif "Sticker" == msg_type:
            sent_msg = await client.send_sticker(chat, file, reply_to_message_id=message.id)

        elif "Voice" == msg_type:
            sent_msg = await client.send_voice(
                chat, file, caption=caption, 
                reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, 
                progress=progress, progress_args=[message, f"_{file_num}_up", user_id, db, start_time, file_num]
            )

        elif "Photo" == msg_type:
            sent_msg = await client.send_photo(chat, file, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

    except Exception as e:
        err_text = str(e)
        if "STOP_TRANSMISSION" in err_text or "NoneType" in err_text:
            try:
                if getattr(smsg, 'id', None):
                    await smsg.edit("**🛑 Batch Stopped Mid-Upload.**")
            except:
                pass
            return # Exit Track 2 immediately
        elif ERROR_MESSAGE:
            try:
                m_id = getattr(message, 'id', None)
                if m_id:
                    await client.send_message(user_chat, f"Error: {e}", reply_to_message_id=m_id)
                else:
                    # If message is gone, send error without reply_to
                    await client.send_message(user_chat, f"Error: {e}")
            except:
                pass

    # --- Final Cleanup Section ---
    status_path = f'{message.id}_{file_num}_up.txt'
    if os.path.exists(status_path): 
        print(f"DEBUG [Cleanup]: Deleting status file {status_path}")
        os.remove(status_path)
    else:
        print(f"DEBUG [Cleanup]: Status file {status_path} was ALREADY GONE.")

    if os.path.exists(file):
        print(f"DEBUG [Cleanup]: Deleting media file {file}")
        os.remove(file)# Protects your 26GB storage

    await client.delete_messages(user_chat, [smsg.id])
    return sent_msg


# get the type of message
def get_message_type(msg: pyrogram.types.messages_and_media.message.Message):
    try:
        msg.document.file_id
        return "Document"
    except:
        pass

    try:
        msg.video.file_id
        return "Video"
    except:
        pass

    try:
        msg.animation.file_id
        return "Animation"
    except:
        pass

    try:
        msg.sticker.file_id
        return "Sticker"
    except:
        pass

    try:
        msg.voice.file_id
        return "Voice"
    except:
        pass

    try:
        msg.audio.file_id
        return "Audio"
    except:
        pass

    try:
        msg.photo.file_id
        return "Photo"
    except:
        pass

    try:
        msg.text
        return "Text"
    except:
        pass


        