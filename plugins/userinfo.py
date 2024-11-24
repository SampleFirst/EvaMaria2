from pyrogram import Client, filters
import datetime
import time
import asyncio
from openpyxl import Workbook
from database.users_chats_db import db
from info import ADMINS
import os

# Excel sheet generation function (only user IDs)
def generate_excel_sheet(user_data):
    wb = Workbook()
    ws = wb.active

    for user in user_data:
        ws.append([user['id']])  # Only append the id
    
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

    # Fetch all users from the database
    users = await db.get_all_users()

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

    # Iterate through each user in the database (up to the specified number)
    async for user in users:
        if done >= num_users:
            break  # Stop once we have processed the requested number of users

        try:
            # Directly process user data, only append id
            user_data.append({
                'id': user['id']
            })
            success += 1
        except Exception as e:
            failed += 1
            print(f"Error processing user {user['id']}: {e}")
        
        done += 1

        # Update progress every 20 users
        if done % 20 == 0:
            await sts.edit(f"In progress:\n\nTotal Users: {total_users}\nCompleted: {done} / {num_users}\nSuccess: {success}\nFailed: {failed}")

        await asyncio.sleep(2)  # Avoid hitting rate limits

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
