from pyrogram import Client, filters
from database.users_chats_db import db
from info import *
import pandas as pd
from datetime import datetime


@Client.on_message(filters.command("export_users"))
async def export_users(client, message):
    # Check if the sender is an admin
    if message.from_user.id not in ADMINS:
        await message.reply("You are not authorized to use this command.")
        return

    # Fetch user IDs from MongoDB asynchronously
    try:
        start_time = datetime.now()  # Start time of the export process
        users_cursor = await db.get_all_users()  # Await the coroutine
        users_list = await users_cursor.to_list(length=None)  # Convert cursor to a list
    except Exception as e:
        await message.reply(f"Error fetching users: {e}")
        return

    if not users_list:
        await message.reply("No user data found in the database.")
        return

    # Prepare a list for user data
    users_data = []
    for user_doc in users_list:
        try:
            # Fetch user info using Telegram API
            user = await client.get_users(user_doc["id"])  # Ensure ID field matches the database schema
            users_data.append({
                "User ID": user.id,
                "Username": user.username or "N/A",
                "First Name": user.first_name or "N/A",
                "Last Name": user.last_name or "N/A",
                "Phone Number": user.phone_number or "N/A",
                "Database Timestamp": user_doc.get("timestamp", "N/A"),  # Include stored timestamp if available
            })
        except Exception as e:
            print(f"Error fetching data for user ID {user_doc['id']}: {e}")
            continue

    if not users_data:
        await message.reply("Could not fetch any user details.")
        return

    # Create a DataFrame for user data
    df = pd.DataFrame(users_data)

    # Add total users and extraction timing as additional data
    total_users = len(users_data)
    end_time = datetime.now()  # End time of the export process
    extraction_time = (end_time - start_time).total_seconds()

    # Add a summary sheet to the Excel file
    summary_data = {
        "Metric": ["Total Users", "Extraction Start Time", "Extraction End Time", "Extraction Duration (seconds)"],
        "Value": [total_users, start_time.strftime("%Y-%m-%d %H:%M:%S"), end_time.strftime("%Y-%m-%d %H:%M:%S"), extraction_time],
    }
    summary_df = pd.DataFrame(summary_data)

    # Generate an Excel file with multiple sheets
    file_path = "user_data.xlsx"
    with pd.ExcelWriter(file_path) as writer:
        df.to_excel(writer, index=False, sheet_name="User Data")
        summary_df.to_excel(writer, index=False, sheet_name="Summary")

    # Send the Excel file to the admin
    await client.send_document(chat_id=message.chat.id, document=file_path)
    await message.reply(f"User data has been exported successfully. Total users: {total_users}.")
