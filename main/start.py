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
from .strings import HELP_TXT
from bot import RazzeshUser

class batch_temp(object):
    IS_BATCH = {}

# download status
async def downstatus(client, statusfile, message, chat, file_num):
    while True:
        if os.path.exists(statusfile): break
        await asyncio.sleep(3)
    while os.path.exists(statusfile):
        with open(statusfile, "r") as f:
            txt = f.read()
        try:
            # Added a header for the Download phase
            await client.edit_message_text(chat, message.id, f"📥 **Downloading File No {file_num}...**\n\n{txt}")
            await asyncio.sleep(10) # Throttle to avoid FloodWait
        except:
            await asyncio.sleep(5)


# upload status
async def upstatus(client, statusfile, message, chat, file_num):
    while True:
        if os.path.exists(statusfile): break
        await asyncio.sleep(3)      
    while os.path.exists(statusfile):
        with open(statusfile, "r") as f:
            txt = f.read()
        try:
            # Added a header for the Upload phase
            await client.edit_message_text(chat, message.id, f"📤 **Uploading File No {file_num}...**\n\n{txt}")
            await asyncio.sleep(10)
        except:
            await asyncio.sleep(5)


# start command
@Client.on_message(filters.command(["start"]))
async def send_start(client: Client, message: Message):
    print("DEBUG: Start command received!")
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
    
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
	
#settings command
@Client.on_callback_query(filters.regex("settings_home"))
async def settings_menu(client, callback_query):
    buttons = [[
        InlineKeyboardButton("📝 Set Custom Caption", callback_data="set_caption_action")
      ],[
		InlineKeyboardButton("📤 Customized Upload", callback_data="set_upload_action")
	  ],[
          InlineKeyboardButton("⚡ Parallel Batch", callback_data="parallel_settings")
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
    user_id = callback_query.from_user.id
    
    # 1. Update status in DB so bot knows to catch the next message
    await db.set_status(user_id, "uploading_caption")
    
    # 2. Inform user (The bot finishes here and waits for a new message)
    await callback_query.message.edit_text(
        "**📝 Custom Caption Settings**\n\n"
        "Send the new caption you want to use. You can use these options:\n"
        "• `{caption}` - To keep the original text and add yours.\n"
        "• `off` - To turn off custom captions completely.\n"
        "• `/cancel` - To stop and go back.\n\n"
        "**Send your caption now:**",
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
	
# help command
@Client.on_message(filters.command(["help"]))
async def send_help(client: Client, message: Message):
    await client.send_message(
        chat_id=message.chat.id, 
        text=f"{HELP_TXT}"
    )
	
#batch command 
@Client.on_message(filters.command("batch") & filters.private)
async def batch_cmd(client, message):
    user_id = message.from_user.id
    
    # Initialize batch data in DB
    # Format: {"link": None, "retries": 0}
    await db.set_batch_data(user_id, {"link": None, "retries": 0})
    
    # Set the state so the 'Catcher' knows to look for a link
    await db.set_status(user_id, "awaiting_start_link")
    
    await message.reply(
        "📦 **Batch Mode Started**\n\n"
        "Please send the **Starting Post Link**.\n\n"
        "• You have **2 attempts** to provide a valid link.\n"
        "• Type `/cancel` to abort."
    )

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
@Client.on_message(filters.text & filters.private, group=-1)
async def handle_user_states(client, message):
    user_id = message.from_user.id
    status = await db.get_status(user_id)

    # --- Section 1: Handle Custom Caption States ---
    if status == "uploading_caption":
        if message.text.lower() == "/cancel":
            await db.set_status(user_id, None)
            
            # Check if a process is active
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
                await message.reply("**✅ Caption menu cancelled.**")

            message.stop_propagation()
            return 

        elif message.text.lower() == "off":
            await db.set_custom_caption(user_id, "off")
            await db.set_status(user_id, None)
            await message.reply("**❌ Custom caption disabled.**")
            message.stop_propagation()
            return
        else:
            await db.set_custom_caption(user_id, message.text)
            await db.set_status(user_id, None)
            await message.reply("**✅ Custom caption saved!**")
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
                    acc = Client("saverestricted", session_string=user_data, api_hash=api_hash, api_id=api_id)
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
                acc = Client("saverestricted", session_string=user_data, api_hash=api_hash, api_id=api_id)
                await acc.connect()
            else:
                acc = RazzeshUser

            await db.set_status(user_id, "processing_batch")
            await run_batch(client, acc, message, start_link, count=count)
            message.stop_propagation()			
            
        except Exception as e:
            await db.set_status(user_id, None)
            await message.reply(f"❌ **Error:** {str(e)}")
            message.stop_propagation()			
            
        message.stop_propagation()
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
            user_data = await db.get_session(message.from_user.id)
            if user_data is None:
                await message.reply("**For Downloading Restricted Content You Have To /login First.**")
                return
            api_id = int(await db.get_api_id(message.from_user.id))
            api_hash = await db.get_api_hash(message.from_user.id)
            try:
                acc = Client("saverestricted", session_string=user_data, api_hash=api_hash, api_id=api_id)
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
async def upload_worker(client, acc, message, upload_queue, stats_msg, total_count):
    """The Upload Lane: Processes files one by one in FIFO order"""
    while True:
        data = await upload_queue.get()
        if data is None: # Shutdown signal
            break
        
        file_path, file_num, start_time, chat_id, msg_id = data
        try:
            # We call handle_private with 'upload_only_file' to skip download phase
            await handle_private(client, acc, message, chat_id, msg_id, start_time, file_num, upload_only_file=file_path)
            
            # Update the batch status message after each successful upload
            await stats_msg.edit_text(f"📊 **Batch Progress:** {file_num}/{total_count} files processed.")
        except Exception as e:
            print(f"Upload Track Error on File {file_num}: {e}")
        finally:
            upload_queue.task_done() # Clears the slot for the next file
            

# run batch helper function
async def run_batch(client, acc, message, start_link, count):
    user_id = message.from_user.id
    base_id = int(start_link.split('/')[-1])
    chat_id = start_link.split('/')[-2]
    batch_start_time = time.time()
    
    if chat_id.isdigit():
        chat_id = int("-100" + chat_id)
    
    # 1. INITIALIZE RAILWAY TRACKS
    # The Queue acts as the 'buffer' between download and upload lanes
    upload_queue = asyncio.Queue(maxsize=1) 
    parallel_on = await db.get_parallel_status(user_id) 
    
    stats_msg = await message.reply(f"📊 **Batch Started:** 0/{count} files processed.")
    
    # 2. START THE UPLOAD WORKER (TRACK 2)
    uploader = asyncio.create_task(upload_worker(client, acc, message, upload_queue, stats_msg, count))
    
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
                await stats_msg.edit_text(f"🛑 **Batch Cancelled!** Processed {i-1}/{count} files.")
                break 

            try:
                # 5. DOWNLOAD LANE (TRACK 1)
                # 'download_only=True' tells handle_private to stop after saving the file
                file_path = await handle_private(client, acc, message, chat_id, current_msg_id, batch_start_time, file_num, download_only=True)
                
                if file_path and os.path.exists(file_path):
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
                    await stats_msg.edit_text(f"🛑 **Batch Cancelled!** Processed {i-1}/{count} files.")
                    break 
                
                print(f"Batch Item Error: {e}")
                continue
        
        # 8. SIGNAL WORKER TO SHUTDOWN AFTER ALL FILES QUEUED
        await upload_queue.put(None) 
        await uploader
        await stats_msg.reply("✅ **Batch Processing Complete!**")

    finally:
        # 9. CLEAN UP STATE AND SESSION
        batch_temp.IS_BATCH[user_id] = True
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
            with open(f'{message.id}{type}status.txt', "w") as fileup:
                fileup.write(tmp)
            # FORCE a final update at 100%
            if current == total:
                await asyncio.sleep(1) 
        except Exception as e:
            print(f"File Write Error: {e}")
            pass


# handle private
async def handle_private(client: Client, acc, message: Message, chatid: int, msgid: int, batch_time=None, file_num=1, download_only=False, upload_only_file=None):
    msg: Message = await acc.get_messages(chatid, msgid)
    if msg.empty: return 
    msg_type = get_message_type(msg)
    if not msg_type: return 

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
        asyncio.create_task(downstatus(client, f'{message.id}downstatus.txt', smsg, user_chat, file_num))

        try:
            start_time = batch_time if batch_time else time.time()
            file = await acc.download_media(
                msg, 
                progress=progress, 
                progress_args=[message, "down", user_id, db, start_time, file_num]
            )
            if os.path.exists(f'{message.id}downstatus.txt'):
                os.remove(f'{message.id}downstatus.txt')
            try:
                await smsg.edit(f"✅ **Download No {file_num} Finished!**\n📦 **Track 1:** Station clear.\n🚀 **Track 2:** Handing over to Upload Lane...")
            except:
                pass

            if download_only:
                return file    
        except Exception as e:
            if str(e) == "STOP_TRANSMISSION":
                await smsg.edit("**🛑 Batch Stopped Mid-Download.**")
                return
            elif ERROR_MESSAGE:
                await client.send_message(user_chat, f"Error: {e}", reply_to_message_id=message.id) 
            if os.path.exists(f'{message.id}downstatus.txt'):
                os.remove(f'{message.id}downstatus.txt')
            return await smsg.delete()

    if goto_upload:
        smsg = await client.send_message(user_chat, '📤 **Preparing Upload...**', reply_to_message_id=message.id) 
    asyncio.create_task(upstatus(client, f'{message.id}upstatus.txt', smsg, user_chat, file_num))

    user_custom = await db.get_custom_caption(user_id)
    original_caption = msg.caption if msg.caption else ""
    if user_custom and user_custom.lower() != "off":
        caption = user_custom.replace("{caption}", original_caption) if "{caption}" in user_custom else user_custom
    else:
        caption = original_caption

    # --- Unified Upload Logic with Kill Switch ---
    try:
        start_time = batch_time if batch_time else time.time()
        if "Document" == msg_type:
            try:
                ph_path = await acc.download_media(msg.document.thumbs[0].file_id)
            except:
                ph_path = None
            await client.send_document(
                chat, file, thumb=ph_path, caption=caption, 
                reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, 
                progress=progress, progress_args=[message, "up", user_id, db, start_time, file_num]
            )
            if ph_path: os.remove(ph_path)

        elif "Video" == msg_type:
            try:
                ph_path = await acc.download_media(msg.video.thumbs[0].file_id)
            except:
                ph_path = None   
            await client.send_video(
                chat, file, duration=msg.video.duration, width=msg.video.width, 
                height=msg.video.height, thumb=ph_path, caption=caption, 
                reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, 
                progress=progress, progress_args=[message, "up", user_id, db, start_time, file_num]
            )
            if ph_path: os.remove(ph_path)

        elif "Audio" == msg_type:
            try:
                ph_path = await acc.download_media(msg.audio.thumbs[0].file_id)
            except:
                ph_path = None
            await client.send_audio(
                chat, file, thumb=ph_path, caption=caption, 
                reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, 
                progress=progress, progress_args=[message, "up", user_id, db, start_time, file_num]
            )
            if ph_path: os.remove(ph_path)

        elif "Animation" == msg_type:
            await client.send_animation(chat, file, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

        elif "Sticker" == msg_type:
            await client.send_sticker(chat, file, reply_to_message_id=message.id)

        elif "Voice" == msg_type:
            await client.send_voice(
                chat, file, caption=caption, 
                reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML, 
                progress=progress, progress_args=[message, "up", user_id, db, start_time, file_num]
            )

        elif "Photo" == msg_type:
            await client.send_photo(chat, file, caption=caption, reply_to_message_id=message.id, parse_mode=enums.ParseMode.HTML)

    except Exception as e:
        if str(e) == "STOP_TRANSMISSION":
            await smsg.edit("**🛑 Batch Stopped Mid-Upload.**")
        elif ERROR_MESSAGE:
            await client.send_message(user_chat, f"Error: {e}", reply_to_message_id=message.id)

    # --- Final Cleanup Section ---
    if os.path.exists(f'{message.id}upstatus.txt'): 
        os.remove(f'{message.id}upstatus.txt')

    if os.path.exists(file):
        os.remove(file) # Protects your 26GB storage

    await client.delete_messages(user_chat, [smsg.id])


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


        