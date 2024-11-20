import os
from pyrogram import Client, filters, enums
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from utils import extract_user
import logging
from datetime import datetime
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

@Client.on_message(filters.command(["userinfo"]))
async def userinfo(client, message):
    # Send a processing status message
    status_message = await message.reply_text("`Fetching user info...`")
    await status_message.edit("`Processing user info...`")

    from_user = None
    from_user_id, _ = extract_user(message)
    try:
        # Fetch user details
        from_user = await client.get_users(from_user_id)
    except Exception as error:
        await status_message.edit(str(error))
        return

    if from_user is None:
        return await status_message.edit("No valid user_id or message specified")

    # Build the user information string
    message_out_str = ""
    message_out_str += f"<b>➲ First Name:</b> {from_user.first_name}\n"
    last_name = from_user.last_name or "<b>None</b>"
    message_out_str += f"<b>➲ Last Name:</b> {last_name}\n"
    message_out_str += f"<b>➲ Telegram ID:</b> <code>{from_user.id}</code>\n"
    username = from_user.username or "<b>None</b>"
    message_out_str += f"<b>➲ User Name:</b> @{username}\n"

    # Check if the user has a premium account
    is_premium = "Yes" if from_user.is_premium else "No"
    message_out_str += f"<b>➲ Premium User:</b> {is_premium}\n"

    # Fetch the user's phone number if available
    phone_number = from_user.phone_number or "<b>None</b>"
    message_out_str += f"<b>➲ Phone Number:</b> {phone_number}\n"

    # Add user link
    message_out_str += f"<b>➲ User Link:</b> <a href='tg://user?id={from_user.id}'><b>Click Here</b></a>\n"

    # Check if the message is from a group or channel and fetch additional details
    if message.chat.type in (enums.ChatType.SUPERGROUP, enums.ChatType.CHANNEL):
        try:
            chat_member_p = await message.chat.get_member(from_user.id)
            joined_date = (chat_member_p.joined_date or datetime.now()).strftime("%Y.%m.%d %H:%M:%S")
            message_out_str += f"<b>➲ Joined this Chat on:</b> <code>{joined_date}</code>\n"
        except UserNotParticipant:
            pass

    # Handle user profile photo
    chat_photo = from_user.photo
    buttons = [[InlineKeyboardButton('🔐 Close', callback_data='close_data')]]
    reply_markup = InlineKeyboardMarkup(buttons)

    if chat_photo:
        # Download and send the user's profile photo
        local_user_photo = await client.download_media(chat_photo.big_file_id)
        await message.reply_photo(
            photo=local_user_photo,
            quote=True,
            reply_markup=reply_markup,
            caption=message_out_str,
            parse_mode=enums.ParseMode.HTML,
            disable_notification=True
        )
        os.remove(local_user_photo)
    else:
        # Send text message without photo
        await message.reply_text(
            text=message_out_str,
            reply_markup=reply_markup,
            quote=True,
            parse_mode=enums.ParseMode.HTML,
            disable_notification=True
        )

    await status_message.delete()