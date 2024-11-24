from pyrogram import Client, filters
import datetime
import time
import asyncio
from openpyxl import Workbook
from database.users_chats_db import db  # Your MongoDB collection
from info import ADMINS
import os


# Excel sheet generation function (user IDs and other data)
def generate_excel_sheet(user_data):
    wb = Workbook()
    ws = wb.active
    ws.append(["User ID", "Username", "First Name", "Premium Status", "Phone Number", "Active User", "Is Deleted", "Last Online Date"])  # Add headers

    for user in user_data:
        ws.append([
            user['id'],
            user['username'],
            user['first_name'],
            user['is_premium'],
            user['phone_number'],
            user['active_user'],
            user['is_deleted'],
            user['last_online_date']
        ])  # Append user data

    file_path = "user_data.xlsx"
    wb.save(file_path)
    return file_path


@Client.on_message(filters.command("getlist") & filters.user(ADMINS))
async def getlist(bot, message):
    # Extract the number of users to fetch from the message
    command_parts = message.text.split()
    num_users = 50  # Default number of users to fetch
    if len(command_parts) > 1 and command_parts[1].isdigit():
        num_users = int(command_parts[1])

    # Fetch user IDs from the database
    users = await db.get_all_users()  # Assuming this returns user IDs and other minimal info

    # Send initial message to inform the admin about the process
    sts = await message.reply_text(
        text=f'Generating user data Excel sheet for {num_users} users...'
    )

    start_time = time.time()
    total_users = await db.total_users_count()
    done = 0
    success = 0
    failed = 0

    user_data = []  # Store user data to be written into the Excel sheet

    async def process_user(user):
        nonlocal success, failed
        try:
            user_info = await bot.get_users(user['id'])  # Fetch user details using the user ID
            now = datetime.datetime.now()

            # Check if the user is active in the last 30 days
            active_user = False
            last_online_date = "N/A"
            if hasattr(user_info, 'status') and user_info.status and user_info.status.is_recent():
                last_online_date = user_info.status.was_online.strftime('%Y-%m-%d %H:%M:%S')
                active_user = (now - user_info.status.was_online).days <= 30

            # Check if the user is deleted
            is_deleted = user_info.is_deleted

            # Append user data
            user_data.append({
                'id': user_info.id,
                'username': user_info.username if user_info.username else 'N/A',
                'first_name': user_info.first_name if user_info.first_name else 'N/A',
                'is_premium': user_info.is_premium if hasattr(user_info, 'is_premium') else False,
                'phone_number': user_info.phone_number if hasattr(user_info, 'phone_number') else 'N/A',
                'active_user': active_user,
                'is_deleted': is_deleted,
                'last_online_date': last_online_date
            })

            success += 1
        except Exception as e:
            failed += 1
            print(f"Error processing user {user['id']}: {e}")

    # Process users in chunks
    chunk_size = 20
    user_chunks = [users[i:i + chunk_size] for i in range(0, min(num_users, len(users)), chunk_size)]

    for chunk in user_chunks:
        tasks = [process_user(user) for user in chunk]
        await asyncio.gather(*tasks)
        done += len(chunk)

        # Update progress message
        await sts.edit(f"In progress:\n\nTotal Users: {total_users}\nCompleted: {done} / {num_users}\nSuccess: {success}\nFailed: {failed}")

    # Generate the Excel file once user data is collected
    file_path = generate_excel_sheet(user_data)
    time_taken = datetime.timedelta(seconds=int(time.time() - start_time))

    # Send the Excel file to the admin
    await bot.send_document(
        chat_id=message.chat.id,
        document=file_path,
        caption=f"Completed:\nCompleted in {time_taken} seconds.\n\nTotal Users: {total_users}\nCompleted: {done} / {num_users}\nSuccess: {success}\nFailed: {failed}"
    )

    # Cleanup (delete the generated file from server if necessary)
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"Error deleting the file: {e}")
