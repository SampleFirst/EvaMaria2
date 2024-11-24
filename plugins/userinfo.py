from pyrogram import Client, filters
import datetime
import time
import asyncio
from openpyxl import Workbook
from database.users_chats_db import db  # Your MongoDB collection
from info import ADMINS
import os

# Excel sheet generation function (user IDs and other data)
def generate_excel_sheet(ws, user_data):
    for user in user_data:
        ws.append([user['id'], user['username'], user['first_name'], user['is_premium'], user['phone_number'], user['active_users'], user['is_deleted'], user['last_online_date']])
    
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

    # Initialize workbook and worksheet
    wb = Workbook()
    ws = wb.active
    ws.append(["User ID", "Username", "First Name", "Premium Status", "Phone Number", "Active Users", "Is Deleted", "Last Online Date"])  # Add headers

    # Iterate through each user in the database (up to the specified number)
    async for user in users:
        if done >= num_users:
            break  # Stop once we have processed the requested number of users

        try:
            # Fetch full user data from Pyrogram using the user ID from the database
            user_info = await bot.get_users(user['id'])  # Fetch user details using the user ID
            
            # Create user data dictionary
            user_data = {
                'id': user_info.id,  # Get user ID from Pyrogram
                'username': user_info.username if user_info.username else 'N/A',  # Get username if available
                'first_name': user_info.first_name if user_info.first_name else 'N/A',  # Get first name if available
                'is_premium': user_info.is_premium if hasattr(user_info, 'is_premium') else False,  # Check if user is premium
                'phone_number': user_info.phone_number if user_info.phone_number else 'N/A',  # Get phone number if available
                'active_users': user_info.status if hasattr(user_info, 'status') and user_info.status == "active" else False,  # Check if user is active
                'is_deleted': user_info.is_deleted if hasattr(user_info, 'is_deleted') else False,  # Check if user is deleted
                'last_online_date': user_info.last_online_date if hasattr(user_info, 'last_online_date') else 'N/A'  # Get last online date if available
            }
            
            # Add user data to worksheet
            ws.append([user_data['id'], user_data['username'], user_data['first_name'], user_data['is_premium'], user_data['phone_number'], user_data['active_users'], user_data['is_deleted'], user_data['last_online_date']])
            
            success += 1
        except Exception as e:
            failed += 1
            print(f"Error processing user {user['id']}: {e}")
        
        done += 1

        # Calculate progress
        progress = (done / num_users) * 100
        time_taken = time.time() - start_time
        approx_time_remaining = (time_taken / done) * (num_users - done)

        # Update progress every 5 users
        if done % 5 == 0:
            await sts.edit(f"In progress:\n\nTotal Users: {total_users}\nCompleted: {done} / {num_users} ({progress:.2f}%)\nSuccess: {success}\nFailed: {failed}\nApprox. Time Remaining: {str(datetime.timedelta(seconds=int(approx_time_remaining)))}")

    # Save the Excel file once user data collection is complete
    file_path = generate_excel_sheet(ws, user_data)
    total_time_taken = datetime.timedelta(seconds=int(time.time() - start_time))

    # Send the Excel file to the admin
    await bot.send_document(
        chat_id=message.chat.id,
        document=file_path,
        caption=f"Completed:\nCompleted in {total_time_taken} seconds.\n\nTotal Users: {total_users}\nCompleted: {done} / {num_users} ({progress:.2f}%)\nSuccess: {success}\nFailed: {failed}"
    )

    # Cleanup (delete the generated file from server if necessary)
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"Error deleting the file: {e}")
