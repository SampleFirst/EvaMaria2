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
    ws.append(["User ID", "Username", "First Name", "Premium Status", "Phone Number", "Status"])  # Add headers

    for user in user_data:
        ws.append([user['id'], user['username'], user['first_name'], user['is_premium'], user['phone_number'], user['status']])  # Append user data
    
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

    # Iterate through each user in the database (up to the specified number)
    async for user in users:
        if done >= num_users:
            break  # Stop once we have processed the requested number of users

        try:
            # Fetch full user data from Pyrogram using the user ID from the database
            user_info = await bot.get_users(user['id'])  # Fetch user details using the user ID
            
            # Create user data dictionary
            user_data.append({
                'id': user_info.id,  # Get user ID from Pyrogram
                'username': user_info.username if user_info.username else 'N/A',  # Get username if available
                'first_name': user_info.first_name if user_info.first_name else 'N/A',  # Get first name if available
                'status': user_info.status if user_info.status else 'N/A',  # Get user status if available
                'is_premium': user_info.is_premium if hasattr(user_info, 'is_premium') else False,  # Check if user is premium
                'phone_number': user_info.phone_number if user_info.phone_number else 'N/A'  # Get phone number if available
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
