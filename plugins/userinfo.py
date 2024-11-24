from pyrogram import Client, filters
import datetime
import time
from openpyxl import Workbook
from database.users_chats_db import db
from info import ADMINS
import os

# Function to generate an Excel sheet
def generate_excel_sheet(ws, user_data):
    # Write headers
    ws.append([
        "User ID", "Username", "First Name", "Premium Status", "Phone Number",
        "Active Users", "Is Deleted", "Last Online Date", "Next Offline Date"
    ])
    # Write user data
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
    # Save the workbook
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
    else:
        return None, None

# Command handler to generate user list
@Client.on_message(filters.command("getlist") & filters.user(ADMINS))
async def getlist(bot, message):
    # Parse the command to get the number of users
    command_parts = message.text.split()
    num_users = 50  # Default number of users
    if len(command_parts) > 1 and command_parts[1].isdigit():
        num_users = int(command_parts[1])

    # Notify admin that the process is starting
    sts = await message.reply_text(
        text=f'Generating user data Excel sheet for {num_users} users...'
    )

    start_time = time.time()
    total_users = await db.total_users_count()  # Get total user count
    done = 0
    success = 0
    failed = 0

    # Initialize workbook and worksheet
    wb = Workbook()
    ws = wb.active

    # Collect user data
    user_data_list = []

    # Iterate through users in the database
    async for user in db.get_all_users():
        if done >= num_users:
            break

        try:
            # Fetch user info from Pyrogram
            user_info = await bot.get_users(user['id'])

            # Parse user status
            last_online_date, next_offline_date = parse_user_status(user_info.status)

            # Create a dictionary with user details
            user_data = {
                'id': user_info.id,
                'username': user_info.username if user_info.username else 'N/A',
                'first_name': user_info.first_name if user_info.first_name else 'N/A',
                'is_premium': getattr(user_info, 'is_premium', False),
                'phone_number': getattr(user_info, 'phone_number', 'N/A'),
                'active_users': user_info.status if user_info.status == "active" else False,
                'is_deleted': getattr(user_info, 'is_deleted', False),
                'last_online_date': last_online_date if last_online_date else 'N/A',
                'next_offline_date': next_offline_date if next_offline_date else 'N/A'
            }

            # Add to list
            user_data_list.append(user_data)
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
            await sts.edit(
                f"In progress:\n\nTotal Users: {total_users}\nCompleted: {done} / {num_users} ({progress:.2f}%)\n"
                f"Success: {success}\nFailed: {failed}\nApprox. Time Remaining: "
                f"{str(datetime.timedelta(seconds=int(approx_time_remaining)))}"
            )

    # Generate Excel sheet
    file_path = generate_excel_sheet(ws, user_data_list)
    total_time_taken = datetime.timedelta(seconds=int(time.time() - start_time))

    # Send the Excel file to admin
    await bot.send_document(
        chat_id=message.chat.id,
        document=file_path,
        caption=f"Completed in {total_time_taken}.\n\nTotal Users: {total_users}\nCompleted: {done} / {num_users} ({progress:.2f}%)\n"
                f"Success: {success}\nFailed: {failed}"
    )

    # Cleanup the file
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"Error deleting the file: {e}")
