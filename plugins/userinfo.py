from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import datetime
import time
from openpyxl import Workbook
from database.users_chats_db import db
from info import ADMINS
import os

# In-memory dictionary to manage cancellation
cancel_requests = {}

# Function to generate an Excel sheet
def generate_excel_sheet(ws, user_data):
    ws.append([
        "User ID", "Username", "First Name", "Premium Status", "Phone Number",
        "Active Users", "Is Deleted", "Last Online Date", "Next Offline Date"
    ])
    for user in user_data:
        ws.append([
            user['id'],
            user['username'],
            user['first_name'],
            user['is_premium'],
            user['phone_number'],
            user['active_users'],
            user['is_deleted'],
            user['last_online_date'],
            user['next_offline_date']
        ])
    file_path = "user_data.xlsx"
    ws.parent.save(file_path)
    return file_path

# Function to parse user status
def parse_user_status(user_status):
    if user_status is None:
        return None, None
    if user_status == "online":
        return None, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    elif user_status == "offline":
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), None
    return None, None

# Command handler to generate user list
@Client.on_message(filters.command("getlist") & filters.user(ADMINS))
async def getlist(bot, message):
    global cancel_requests

    # Parse the command for the number of users
    command_parts = message.text.split()
    num_users = 50  # Default
    if len(command_parts) > 1 and command_parts[1].isdigit():
        num_users = int(command_parts[1])

    # Notify admin and provide a cancel button
    sts = await message.reply_text(
        text=f"Generating user data Excel sheet for {num_users} users...",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Cancel", callback_data=f"cancel_getlist_{message.chat.id}")]
        ])
    )

    # Add the request to the cancel_requests dictionary
    cancel_requests[message.chat.id] = False

    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    success = 0
    failed = 0

    wb = Workbook()
    ws = wb.active
    user_data_list = []

    try:
        users = await db.get_all_users()  # Await the coroutine
        async for user in users:
            if cancel_requests[message.chat.id]:  # Check if cancellation is requested
                await sts.edit("Process canceled by admin.")
                del cancel_requests[message.chat.id]
                return

            if done >= num_users:
                break

            try:
                user_info = await bot.get_users(user['id'])
                last_online_date, next_offline_date = parse_user_status(user_info.status)
                user_data = {
                    'id': user_info.id,
                    'username': user_info.username or 'N/A',
                    'first_name': user_info.first_name or 'N/A',
                    'is_premium': getattr(user_info, 'is_premium', False),
                    'phone_number': getattr(user_info, 'phone_number', 'N/A'),
                    'active_users': user_info.status == "active",
                    'is_deleted': getattr(user_info, 'is_deleted', False),
                    'last_online_date': last_online_date or 'N/A',
                    'next_offline_date': next_offline_date or 'N/A'
                }
                user_data_list.append(user_data)
                success += 1
            except Exception as e:
                failed += 1
                print(f"Error processing user {user['id']}: {e}")

            done += 1
            progress = (done / num_users) * 100
            time_taken = time.time() - start_time
            approx_time_remaining = (time_taken / done) * (num_users - done)
            if done % 5 == 0:
                await sts.edit(
                    f"In progress:\n\nTotal Users: {total_users}\nCompleted: {done} / {num_users} ({progress:.2f}%)\n"
                    f"Success: {success}\nFailed: {failed}\nApprox. Time Remaining: "
                    f"{str(datetime.timedelta(seconds=int(approx_time_remaining)))}"
                )

        file_path = generate_excel_sheet(ws, user_data_list)
        total_time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
        await bot.send_document(
            chat_id=message.chat.id,
            document=file_path,
            caption=f"Completed in {total_time_taken}.\n\nTotal Users: {total_users}\nCompleted: {done} / {num_users} ({progress:.2f}%)\n"
                    f"Success: {success}\nFailed: {failed}"
        )
    finally:
        # Cleanup
        del cancel_requests[message.chat.id]
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting the file: {e}")

# Callback handler to handle cancel button
@Client.on_callback_query(filters.regex(r"^cancel_getlist_"))
async def cancel_getlist(bot, callback_query):
    global cancel_requests
    chat_id = int(callback_query.data.split("_")[-1])
    cancel_requests[chat_id] = True
    await callback_query.message.edit("Canceling process. Please wait...")
