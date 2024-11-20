import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users_chats_db import db
import logging
import openpyxl

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

@Client.on_message(filters.command(["extract_users"]))
async def extract_users(client, message):
    # Send a processing status message
    status_message = await message.reply_text("`Fetching user data...`")

    try:
        # Fetch 10 users from the database
        users = await db.get_users(10)  # Replace with your actual database query to fetch users
        if not users:
            await status_message.edit("No users found in the database.")
            return

        # Create an Excel workbook
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "User Data"

        # Add headers to the Excel sheet
        headers = ["Telegram ID", "First Name", "Last Name", "Username", "Phone Number", "Premium User"]
        sheet.append(headers)

        # Add user data to the sheet
        for user in users:
            telegram_id = user.get("id", "N/A")
            first_name = user.get("first_name", "N/A")
            last_name = user.get("last_name", "N/A")
            username = user.get("username", "N/A")
            phone_number = user.get("phone_number", "N/A")
            is_premium = "Yes" if user.get("is_premium", False) else "No"

            sheet.append([telegram_id, first_name, last_name, username, phone_number, is_premium])

        # Save the workbook to a file
        file_name = "user_data.xlsx"
        workbook.save(file_name)

        # Send the file to the user
        await client.send_document(
            chat_id=message.chat.id,
            document=file_name,
            caption="Here is the user data you requested.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔐 Close", callback_data="close_data")]
            ])
        )

        # Remove the file after sending
        os.remove(file_name)

        # Delete the status message
        await status_message.delete()

    except Exception as error:
        logger.error(f"Error fetching user data: {error}")
        await status_message.edit(f"An error occurred: {error}")